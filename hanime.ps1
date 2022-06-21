# to autostart this script:
# just put this script into startup folder (%USERPROFILE%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup)
# or use something like nssm (https://nssm.cc/) or the Task Scheduler of Windows

# --------------------------------
# edit the following two variables
# --------------------------------
$pythonPath = "C:\Users\alima\.pyenv\pyenv-win\versions\3.8.10\python.exe"
$workingDir = "C:\Users\alima\MEGAsync\_ProgStuff\hanime-auto-coins-collector\"

Set-Location "$workingDir"
Start-Transcript -path "$workingDir\hanime_log.txt" -append -UseMinimalHeader


function startCoins {
    Write-Output "We're good to go. starting loop..."
    while ($true) {
        Write-Output "trying to get coins... at $(get-date)"
        Invoke-Expression "$pythonPath $workingDir\getcoins.py"
        Write-Output "sleeping for ~3 hours..."
        start-sleep -s "$(get-random -minimum (60*60*3+10) -maximum (60*60*3+100))"
    }   
}

Write-Output "Running once to figure out wait time"
#  regex that matches date like "Tue Jun 21 13:01:29 2022 UTC"
$reg = [regex]::new("\w{3} \w{3} \d{1,2} \d{1,2}:\d{1,2}:\d{1,2} \d{4} UTC")
#  run program and parse the output
Invoke-Expression "$pythonPath $workingDir\getcoins.py" | Select-String ".*" | ForEach-Object {
    #  print output to console
    Write-Output "> $_"
    $val = $reg.Matches($_.Line).Value
    # since this goes line by line, we need to make sure the logic runs only on the line with the date. on every other line $val will be $Null
    if(!($val -eq $Null)){
        # datetime doesn't like UTC as an offset, so we have to replace it by +0
        $val = $val.Replace("UTC","+0")
        # convert string to datetime object
        $lastClick = ([datetime]::ParseExact($val, "ddd MMM dd HH:mm:ss yyyy z", $Null))
        # delay click a bit to make sure delay is over and make the botting less obvious
        $rand = get-random -Minimum 60 -Maximum 240
        $nextClick = $lastClick.AddHours(3).AddSeconds($rand)
        # calculate seconds until 3 hours since last click
        $nextClickSeconds = (New-TimeSpan –End $nextClick).TotalSeconds
        Write-Output "next click is at $($nextClick), which is in $($nextClickSeconds) seconds"
        if ($nextClickSeconds -lt 0) {
            Write-Output "something went wrong. try again."
            exit 1
        }
        Write-Output "waiting for $($nextClickSeconds) seconds"
        Start-Sleep -Seconds $nextClickSeconds
        # after waiting go into main loop
        startCoins
    }
}
Stop-Transcript 