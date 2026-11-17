$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:PYTHONPATH = "$scriptDir\src;$env:PYTHONPATH"
python -m lanerush.cli @args
