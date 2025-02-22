#!/usr/bin/env python3

import subprocess
import os

def getAnswer(text):
    try:
        return input(text)
    except KeyboardInterrupt:
        print("\nCtrl+C pressed, aborting")
        exit(-2)

print("Welcome to the Fugu16 iOS installer.")
print("This script will build and install Fugu16 on your device.")
print("Before continuing, please read the requirements:")
print("    - You need a supported device running a supported iOS version (see README.md)")
print("    - The device must be connected via USB")
print("    - You need the IPSW for your device, *unzipped*")
print("    - You need to have Xcode installed")
print("    - You need to have iproxy and ideviceinstaller installed (brew install usbmuxd ideviceinstaller)")

print("Starting...")



build_jailbreakd = True

csIdentity = "Apple Dev"

    print("Patching arm/iOS/jailbreakd/build.sh...")
    with open("arm/iOS/jailbreakd/build.sh", "r") as f:
        build_sh = f.read()
    
    lines = []
    for line in build_sh.split("\n"):
        if line.startswith("CODESIGN_IDENTITY="):
            lines.append(f'CODESIGN_IDENTITY="{csIdentity}"')
        else:
            lines.append(line)

    with open("arm/iOS/jailbreakd/build.sh", "w") as f:
        f.write("\n".join(lines))

    print("Patched")

    print("Compiling jailbreakd...")

    try:
        subprocess.run(["/bin/bash", "build.sh"], check=True, cwd="arm/iOS/jailbreakd/")
    except subprocess.CalledProcessError as e:
        print(f"Failed to build jailbreakd! Exit status: {e.returncode}")
        exit(-1)

    print("Successfully built jailbreakd")

print("Getting CDHash of jailbreakd...")
try:
    out = subprocess.run(["/usr/bin/codesign", "-dvvv", "arm/iOS/Fugu16App/Fugu16App/jailbreakd"], capture_output=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to get CDHash of jailbreakd! Codesign exit status: {e.returncode}")
    print("stdout:")
    print(e.stdout)
    print("stderr:")
    print(e.stderr)
    exit(-1)

cdhash = None
out = out.stderr.decode("utf8")
for line in out.split("\n"):
    if line.startswith("CDHash="):
        cdhash = line[7:]
        break
        
if cdhash is None:
    print("Error: Codesign did not output the CDHash for jailbreakd!")
    exit(-1)

print(f"CDHash of jailbreakd: {cdhash}")

print("Patching arm/iOS/Fugu16App/Fugu16App/closures.swift...")

with open("arm/iOS/Fugu16App/Fugu16App/closures.swift", "r") as f:
    closure_swift = f.read()

lines = []
for line in closure_swift.split("\n"):
    if line.startswith('        try simpleSetenv("JAILBREAKD_CDHASH", '):
        lines.append (f'        try simpleSetenv("JAILBREAKD_CDHASH", "{cdhash}")')
    else:
        lines.append(line)

with open("arm/iOS/Fugu16App/Fugu16App/closures.swift", "w") as f:
    f.write("\n".join(lines))

print("Patched")

print("Compiling Fugu16App")

try:
    subprocess.run(["xcodebuild", "-scheme", "Fugu16App", "-derivedDataPath", "build"], check=True, cwd="arm/iOS/Fugu16App/")
except subprocess.CalledProcessError as e:
    print(f"Failed to build Fugu16App! Exit status: {e.returncode}")
    print("If the build failed due to a codesign error, open arm/iOS/Fugu16App/Fugu16App.xcodeproj in Xcode")
    print("    and edit the Signing options in the Signing & Capabilities section.")
    exit(-1)

print("Successfully built Fugu16App")

print("Please open the folder containing your unzipped IPSW now.")
print("Afterwards, open the *largest* dmg in it (containing the root file system)")


mntPath = ./.dmg

print("Creating IPAs...")

try:
    subprocess.run(["/bin/bash", "build_ipas.sh", "../arm/iOS/Fugu16App/build/Build/Products/Release-iphoneos/Fugu16App.app", mntPath], check=True, cwd="tools")
except subprocess.CalledProcessError as e:
    print(f"Failed to create IPAs! Exit status: {e.returncode}")
    exit(-1)

print("IPAs created")

print("Please make sure your device is connected via USB, unlocked and paired to this Mac")
getAnswer("Press enter to continue or Ctrl+C to abort...")

print("Removing Fugu16App in case it is installed...")

try:
    subprocess.run(["ideviceinstaller", "-U", "de.linushenze.Fugu16App"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except:
    pass

print("Installing Fugu16 Setup")

try:
    subprocess.run(["ideviceinstaller", "-i", "tools/Fugu16_Setup.ipa"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to install Fugu16App! Exit status: {e.returncode}")
    exit(-1)

print("Successfully installed Fugu16App")
print("Please launch it now on your device and tap on setup")
print("Then wait until you see 'Done. Please update me now.'")
getAnswer("Press enter once you are done or Ctrl+C to abort...")

print("Installing Fugu16 exploit")

try:
    subprocess.run(["ideviceinstaller", "-i", "tools/Fugu16_Pwn.ipa"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to install Fugu16 exploit! Exit status: {e.returncode}")
    exit(-1)

print("\n")
print("Done! Open the Fugu16App again and follow the on-screen instructions!")
print("Once you are jailbroken, have rebooted and unlocked your device, connect to it by running the following commands:")
print("    iproxy 1337 1337  # Terminal Window A")
print("    nc localhost 1337 # Terminal Window B")
print("You should now see a prompt like this: 'iDownload>'. Type 'bash' to get a root shell")
