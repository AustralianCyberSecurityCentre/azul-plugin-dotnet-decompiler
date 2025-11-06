# Azul Plugin Dotnet Decompiler

Decompiles dotnet using ILSpy's commandline tool.

## Installation

### installing dotnet locally (ubuntu22+)

sudo apt install dotnet6
sudo apt install dotnet7

### install tool (if setup.py fails to install it)

ILSpy commandline tool for decompiling
https://github.com/icsharpcode/ILSpy/tree/master/ICSharpCode.ILSpyCmd
dotnet tool install ilspycmd --tool-path /usr/bin/

```
pip install azul-plugin-dotnet-decompiler
```

## Usage

Usage on local files:

```
$ azul-plugin-dotnet-decompiler malware.file
... example output goes here ...
level=INFO time=2023-11-19 20:43:37+0000 name=azul_runner.plugin custom startup options:
level=INFO time=2023-11-19 20:43:37+0000 name=azul_runner.plugin max_file_size       : 10485760
level=INFO time=2023-11-19 20:43:37+0000 name=azul_runner.coordinator received plugin=DotnetDecompiler type=Win32 EXE size=25088 id=9c44230c8e01057143430213fc271fed07a4398b54039980156225d81c184c6c
level=INFO time=2023-11-19 20:43:39+0000 name=azul.plugin.dotnetdecompiler Successfully decompiled and added C# content.
assembly has no entry point
level=INFO time=2023-11-19 20:43:40+0000 name=azul.plugin.dotnetdecompiler Successfully processed IL file.
level=INFO time=2023-11-19 20:43:42+0000 name=azul_runner.coordinator finish plugin=DotnetDecompiler mp=None state=OK type=Win32 EXE size=25088 id=9c44230c8e01057143430213fc271fed07a4398b54039980156225d81c184c6c
level=INFO time=2023-11-19 20:43:42+0000 name=azul_runner.main Processing complete
----- AzulPluginDotnetDecompiler results -----
OK

events (1)

event for binary:9c44230c8e01057143430213fc271fed07a4398b54039980156225d81c184c6c:None
  {}
  output data streams (2):
    17192 bytes - EventData(hash='e26c40d81db42a969d1877890efa7e49e4e284745d83561a32a88d39965cfe24', label='decompiled_cs')
    59 bytes - EventData(hash='b61748d872b25f22d9f7e715933c088628e68b26d493b565835c62d589c1744e', label='cs_call_tree')
  output features:
              assembly_name: dnSpy
           assembly_version: 1.5.0.0
              class_methods: Dispatcher::.ctor
                             Dispatcher::BeginInvoke
                             Dispatcher::CheckAccess
                             Dispatcher::VerifyAccess
                             DnSpyFileListOptionsImpl::.ctor
                             DnSpyFileListOptionsImpl::get_Dispatcher
                             DnSpyFileListOptionsImpl::get_UseDebugSymbols
                             DnSpyFileListOptionsImpl::get_UseGAC
                             DnSpyFileListOptionsImpl::get_UseMemoryMappedIO
                             DnSpyFileListOptionsImpl::set_UseDebugSymbols
                             DnSpyFileListOptionsImpl::set_UseGAC
                             DnSpyFileListOptionsImpl::set_UseMemoryMappedIO
                             ErrorException::.ctor
                             Program::.cctor
                             Program::.ctor
                             Program::DoIt
                             Program::DumpDir
                             Program::DumpDir2
                             Program::DumpEx
                             Program::DumpNetModule
                             Program::GetBaseName
                             Program::GetDirs
                             Program::GetDotNetFiles
                             Program::GetFiles
                             Program::GetLanguage
                             Program::GetProgramBaseName
                             Program::GetProjectDir
                             Program::GetProjectFileName
                             Program::InitILSpy
                             Program::Main
                             Program::OpenNetFile
                             Program::ParseCommandLine
                             Program::PrintHelp
                    classes: Dispatcher
                             DnSpyFileListOptionsImpl
                             ErrorException
                             Program
              compiled_time: 2015-11-26 17:20:33
                       mvid: 859fa593-84b8-409d-8419-0d4731b9a8a5
    namespace_class_methods: Dispatcher::.ctor
                             Dispatcher::BeginInvoke
                             Dispatcher::CheckAccess
                             Dispatcher::VerifyAccess
                             DnSpyFileListOptionsImpl::.ctor
                             DnSpyFileListOptionsImpl::get_Dispatcher
                             DnSpyFileListOptionsImpl::get_UseDebugSymbols
                             DnSpyFileListOptionsImpl::get_UseGAC
                             DnSpyFileListOptionsImpl::get_UseMemoryMappedIO
                             DnSpyFileListOptionsImpl::set_UseDebugSymbols
                             DnSpyFileListOptionsImpl::set_UseGAC
                             DnSpyFileListOptionsImpl::set_UseMemoryMappedIO
                             dnSpyc.ErrorException::.ctor
                             dnSpyc.Program::.cctor
                             dnSpyc.Program::.ctor
                             dnSpyc.Program::DoIt
                             dnSpyc.Program::DumpDir
                             dnSpyc.Program::DumpDir2
                             dnSpyc.Program::DumpEx
                             dnSpyc.Program::DumpNetModule
                             dnSpyc.Program::GetBaseName
                             dnSpyc.Program::GetDirs
                             dnSpyc.Program::GetDotNetFiles
                             dnSpyc.Program::GetFiles
                             dnSpyc.Program::GetLanguage
                             dnSpyc.Program::GetProgramBaseName
                             dnSpyc.Program::GetProjectDir
                             dnSpyc.Program::GetProjectFileName
                             dnSpyc.Program::InitILSpy
                             dnSpyc.Program::Main
                             dnSpyc.Program::OpenNetFile
                             dnSpyc.Program::ParseCommandLine
                             dnSpyc.Program::PrintHelp
          namespace_classes: dnSpyc.ErrorException
                             dnSpyc.Program
          namespace_methods: dnSpyc::.cctor
                             dnSpyc::.ctor
                             dnSpyc::DoIt
                             dnSpyc::DumpDir
                             dnSpyc::DumpDir2
                             dnSpyc::DumpEx
                             dnSpyc::DumpNetModule
                             dnSpyc::GetBaseName
                             dnSpyc::GetDirs
                             dnSpyc::GetDotNetFiles
                             dnSpyc::GetFiles
                             dnSpyc::GetLanguage
                             dnSpyc::GetProgramBaseName
                             dnSpyc::GetProjectDir
                             dnSpyc::GetProjectFileName
                             dnSpyc::InitILSpy
                             dnSpyc::Main
                             dnSpyc::OpenNetFile
                             dnSpyc::ParseCommandLine
                             dnSpyc::PrintHelp
                 namespaces: dnSpyc
           target_framework: ".NETFramework,Version=v4.0,Profile=Client", FrameworkDisplayName = ".NET Framework 4 Client Profile"

Feature key:
  assembly_name:  The name of the decompiled assembly.
  assembly_version:  The version of the assembly.
  class_methods:  All of the class level methods that are present in the decompiled binary.
  classes:  All the classes found in the decompiled binary.
  compiled_time:  Time the binary was compiled.
  mvid:  .NET module version GUID (unique ID to identify the module).
  namespace_class_methods:  All of the fully pathed methods that are present in the decompiled binary.
  namespace_classes:  All the classes with their namespace found in the decompiled binary.
  namespace_methods:  All of namespace level methods that are present in the decompiled binary.
  namespaces:  All the namespaces found in the decompiled binary.
  target_framework:  The target framework of the assembly.
```

Check `azul-plugin-dotnet-decompiler --help` for advanced usage.

## Python Package management

This python package is managed using a `setup.py` and `pyproject.toml` file.

Standardisation of installing and testing the python package is handled through tox.
Tox commands include:

```bash
# Run all standard tox actions
tox
# Run linting only
tox -e style
# Run tests only
tox -e test
```

## Dependency management

Dependencies are managed in the requirements.txt, requirements_test.txt and debian.txt file.

The requirements files are the python package dependencies for normal use and specific ones for tests
(e.g pytest, black, flake8 are test only dependencies).

The debian.txt file manages the debian dependencies that need to be installed on development systems and docker images.

Sometimes the debian.txt file is insufficient and in this case the Dockerfile may need to be modified directly to
install complex dependencies.
