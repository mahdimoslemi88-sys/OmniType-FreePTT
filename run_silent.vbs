' ============================================================================
' OmniType-FreePTT VBScript Silent Launcher
' Spawns pythonw.exe with window style 0 (completely hidden) so no terminal opens.
' ============================================================================
Set WshShell = CreateObject("WScript.Shell")
strDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """" & strDir & "\voice_env\Scripts\pythonw.exe"" """ & strDir & "\OmniType-FreePTT.py""", 0, False
