"""Decompiles dotnet using ILSpy's commandline tool."""

import datetime
import re
import tempfile

from azul_runner import (
    BinaryPlugin,
    DataLabel,
    Feature,
    FeatureType,
    Job,
    State,
    add_settings,
    cmdline_run,
)

from azul_plugin_dotnet_decompiler import il_spy
from azul_plugin_dotnet_decompiler.il_processor import il_analyser
from azul_plugin_dotnet_decompiler.il_processor.getnetguids import (
    get_assembly_guids,
    is_dot_net_assembly,
)


class AzulPluginDotnetDecompiler(BinaryPlugin):
    """Decompiles dotnet using ILSpy's commandline tool."""

    VERSION = "2025.03.18"
    SETTINGS = add_settings(
        filter_max_content_size=(int, 10 * 1024 * 1024),
        # Dotnet can compile to linux or windows
        filter_data_types={
            "content": [
                # Windows exe
                "executable/windows/pe",
                "executable/windows/pe32",
                "executable/windows/pe64",
                "executable/windows/dll",
                "executable/windows/dll32",
                "executable/windows/dll64",
                # Non windows exe
                "executable/dll32",
                "executable/pe32",
                # Linux elf
                "executable/linux/",
            ]
        },
    )
    FEATURES = [
        # Assembly general info
        Feature("assembly_name", desc="The name of the decompiled assembly.", type=FeatureType.String),
        Feature("assembly_version", desc="The version of the assembly.", type=FeatureType.String),
        Feature("target_framework", desc="The target framework of the assembly.", type=FeatureType.String),
        # methods
        Feature(
            "namespace_class_methods",
            desc="All of the fully pathed methods that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        Feature(
            "class_methods",
            desc="All of the class level methods that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        Feature(
            "namespace_methods",
            desc="All of namespace level methods that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        # classes
        Feature("classes", desc="All the classes found in the decompiled binary.", type=FeatureType.String),
        Feature(
            "namespace_classes",
            desc="All the classes with their namespace found in the decompiled binary.",
            type=FeatureType.String,
        ),
        # namespaces
        Feature("namespaces", desc="All the namespaces found in the decompiled binary.", type=FeatureType.String),
        # Other interesting assembly features
        Feature(
            "delegates",
            desc="All of the dotnet delegates that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        Feature(
            "enums", desc="All of the dotnet enums that are present in the decompiled binary.", type=FeatureType.String
        ),
        Feature(
            "structs",
            desc="All of the dotnet structs that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        Feature(
            "interfaces",
            desc="All of the dotnet interfaces that are present in the decompiled binary.",
            type=FeatureType.String,
        ),
        # Package identifiers.
        Feature("mvid", desc=".NET module version GUID (unique ID to identify the module).", type=FeatureType.String),
        Feature(
            "typelib_id", desc=".NET typelib GUID (unique ID to recognised the type library).", type=FeatureType.String
        ),
        Feature("compiled_time", desc="Time the binary was compiled.", type=FeatureType.Datetime),
    ]

    def execute(self, job: Job):
        """Run the plugin."""
        file_path = job.get_data().get_filepath()

        if not is_dot_net_assembly(file_path):
            # Not a dotnet binary, so nothing to do.
            return State(State.Label.OPT_OUT, message="Not a valid dotnet binary.")

        # Decompile CS
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                decompiled_cs_path = il_spy.run_ilspy_decompile(file_path, temp_dir)
            except il_spy.NotDotnetFileError:
                # A malformed dotnet file, because it is a valid dotnet file but something is wrong with it.
                return self.is_malformed("Malformed dotnet file.")
            except il_spy.UnsupportedPEError:
                # A PE file that is not supported by IL spy
                return self.is_malformed("ILSpy could not decompile the PE file it's probably not a dotnet PE.")
            except il_spy.PartialDotnetError:
                # A PE that is a dotnet file but has unexpected issues
                # (this typically occurs on content carved out by other plugins)
                return self.is_malformed(
                    "Only partial Dotnet with bad libraries (typically due to plugins carving up binary)."
                )
            except il_spy.UnknownILSpyError:
                return self.is_malformed(
                    "ILSpy could not decompile the PE file it's probably not a dotnet PE - unknown error."
                )

            with open(decompiled_cs_path, "r") as decompiled_cs_file:
                # Search for assembly info.
                line = decompiled_cs_file.readline()
                find_data = re.compile('(?<=\\()?".*"(?<=\\))?', flags=re.IGNORECASE)
                total_matches = 0
                while line:
                    if "[assembly: AssemblyTitle(" in line:
                        match_data = find_data.search(line)
                        # Match may fail if the title isn't a string e.g [assembly: AssemblyTitle(null)]
                        if match_data:
                            self.add_feature_values("assembly_name", match_data.group().strip('"'))
                            total_matches += 1
                    if "[assembly: AssemblyVersion(" in line:
                        match_data = find_data.search(line)
                        # Match may fail if the title isn't a string e.g [assembly: AssemblyVersion(null)]
                        if match_data:
                            self.add_feature_values("assembly_version", match_data.group().strip('"'))
                            total_matches += 1
                    if "[assembly: TargetFramework(" in line:
                        match_data = find_data.search(line)
                        # Match may fail if the title isn't a string e.g [assembly: TargetFramework(null)]
                        if match_data:
                            self.add_feature_values("target_framework", match_data.group())
                            total_matches += 1

                    # Exit early if we've found everything we want.
                    if total_matches >= 3:
                        break
                    line = decompiled_cs_file.readline()
            with open(decompiled_cs_path, "rb") as decompiled_cs_file:
                self.add_data_file(DataLabel.DECOMPILED_CS, {}, decompiled_cs_file)
            self.logger.info("Successfully decompiled and added C# content.")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Decomile IL
            il_code_path = il_spy.run_ilspy_decompile(file_path, temp_dir, True)
            try:
                analysis_result = il_analyser.parse_il(il_code_path)
                if analysis_result.get("il_analysis", {}).get("call_tree_friendly"):
                    self.add_data(
                        DataLabel.CS_CALL_TREE, {}, str.encode(analysis_result["il_analysis"]["call_tree_friendly"])
                    )
                il_parsed = analysis_result.get("il_parsed", {})
                if len(il_parsed.get("list_ilmethod", [])) > 0:
                    self.parse_il_method_features(il_parsed.get("list_ilmethod"))
                self.logger.info("Successfully processed IL file.")
            except il_analyser.AnalyseException:
                self.logger.warning(f"Failed to get call tree job: '{job.id}'")

        # Extract various types
        for feature_key, ilspy_list_type in [
            ("delegates", il_spy.IlSpyListTypes.DELEGATE),
            ("enums", il_spy.IlSpyListTypes.ENUM),
            ("structs", il_spy.IlSpyListTypes.STRUCT),
            ("interfaces", il_spy.IlSpyListTypes.INTERFACE),
        ]:
            result = il_spy.run_ilspy_list_type(file_path, ilspy_list_type)
            if len(result) > 0:
                self.add_feature_values(feature_key, result)

        # Get assemblyline Guids
        try:
            guids_dict = get_assembly_guids(file_path)

            if guids_dict:
                if guids_dict.get("mvid"):
                    self.add_feature_values("mvid", guids_dict.get("mvid"))

                if guids_dict.get("typelib_id"):
                    self.add_feature_values("typelib_id", guids_dict.get("typelib_id"))

                if guids_dict.get("compiled_time"):
                    self.add_feature_values(
                        "compiled_time", datetime.datetime.fromisoformat(guids_dict.get("compiled_time"))
                    )
        except Exception:
            self.logger.warning(f"Failed to find mvid for job: '{job.id}'")

    def parse_il_method_features(self, il_methods: list[str]):
        """Parse important information from il method strings, and add them as feature values."""
        namespace_class_method_found: set[str] = set()
        namespaces_found: set[str] = set()
        namespace_method_found: set[str] = set()
        namespace_class_found: set[str] = set()
        classes_found: set[str] = set()
        class_method_found: set[str] = set()

        for i in il_methods:
            if i.startswith("'"):
                """
                Imported classes generate weird looking lines like:
                "'<DumpDir>d_22'::'System.Collections.Generic.IEnumerator<ICSharpCode.ILSpy.ProjectInfo>.get_Current'"

                Removing these altogether makes the results far more readable, at the cost of obscuring imported
                    classes from the standard libraries
                Custom imports remain included as they would be parsed separately
                """
                continue

            namespace_class_method_found.add(i)
            fullnamespace_class, method = i.split("::")

            if "." in fullnamespace_class:  # namespace not always included. Can just be class::method
                fullnamespace, _class = fullnamespace_class.rsplit(".", 1)
                namespace_class_found.add(fullnamespace_class)
                namespaces_found.add(fullnamespace)
                namespace_method_found.add(fullnamespace + "::" + method)

                if "." in fullnamespace:  # if there are multiple levels of namespace then get the top level
                    topnamespace = fullnamespace.split(".")[0]
                    namespaces_found.add(topnamespace)

            else:  # no namespace in fullnamespace_class
                _class = fullnamespace_class

            classes_found.add(_class)
            class_method_found.add(_class + "::" + method)

        # Add features
        self.add_feature_values("namespace_class_methods", namespace_class_method_found)
        self.add_feature_values("class_methods", class_method_found)
        self.add_feature_values("namespace_methods", namespace_method_found)

        self.add_feature_values("classes", classes_found)
        self.add_feature_values("namespace_classes", namespace_class_found)

        self.add_feature_values("namespaces", namespaces_found)


def main():
    """Plugin command-line entrypoint."""
    cmdline_run(plugin=AzulPluginDotnetDecompiler)


if __name__ == "__main__":
    main()
