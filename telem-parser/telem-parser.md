# CU-InSpace Telemetry Parser

## Getting Telemetry On to an SD Card

When using the rocket variant of the avionics software, the avionics system will begin recording telemetry to an SD card as soon as it is powered on with a valid SD card inserted. However, the SD card must be properly formatted before the avionics software will see it as valid.

To format an SD card, use the following steps. **NOTE: THESE STEPS WILL OVERWRITE ANY DATA ALREADY ON THE SD CARD**

1. Insert the SD card into the MCU board and connect the MCU board to a computer via USB to power it on.
2. From the MCU board's debugging console, run the command `logging pause` to ensure that the avionics software is not actively writing data to the SD card.
3. From the MCU board's debugging console, run the command `mbr create` to create a new Master Boot Record partition table. The new partition table will have a single CU InSpace data partition starting at block 2048 and taking up the rest of the card.
4. From the MCU board's debugging console, run the command `format 0` to create a super-block in the CU InSpace data partition that we created in the previous step.

Once the SD card is formatted using the above steps the MCU board will need to be reset before it will begin logging data (do not use `logging resume` to restart logging after formatting).

## Getting Telemetry Off of an SD Card

The avionics software uses a custom filesystem format, so getting the telemetry data off the SD card requires reading the raw data from the card. To avoid having to read the entire card when most of the card will usually be empty, we can do this in two steps. First we get just the super-block from the SD card, then we use a script to parse the super-block and tell us how many blocks need to be copied to get all of the data from the card.

To copy raw data from the card we can use the `dd` utility. This utility should be installed by default on macOS or Linux. On Windows you can get `dd` as part of the "Git Bash" shell that comes with Git for Windows.

1. The first step is to determine which drive on your computer is the SD card. How you do this will depend on the operating system you are using:
   - On Linux, run `dmesg` immediately after connecting the SD card to the computer. You will see the path to the disk near the end of the output, it will look something like `/dev/sdf`, where `f` may be a different letter or `/dev/mmcblk8`, where `8` may be a different number.
   - On macOS, use `diskutil list` to show all of the drives connected to the computer, you can determine which one is the SD card based on the size of the disk. The path to the disk will look something like `/dev/disk6` where `6` may be a different number. If you have trouble identifying with disk is the SD card try running `diskutil list` with and without the SD card connected and compare the results.
   - On Windows, open Git Bash and run `cat /proc/partitions` before connecting the SD card and again after connecting the SD card. Look for a new entry with a path that looks something like `/dev/sdf`, where `f` may be a different letter.
2. Copy the super-block from the disk to a file on your computer named `sb` by running `dd if=[disk path] of=sb bs=512 count=1 skip=2048`. Note that you will need to replace `[disk path]` with the path you found in step 1. On macOS and Linux you may need to run this command with `sudo`, on Windows you will need to open Git Bash as an administrator.
3. Use `telem-parser.py` to parse the super-block. Simply run `python3 telem-parser sb`, near the bottom of the output the script will provide an example `dd` command for copying all of the telemetry data from the card. This example command will include a block count.
4. Copy the telemetry data to your computer with the command ` dd if=[disk path] of=full bs=512 count=[count]`. Replace `[disk path]` with the path from step 1 and `[count]` with the number provided by the script in step 3. This will create a file named `full` which contains all of the telemetry data from the card.
5. Parse the telemetry data with the command `python3 telem-parser.py Spaceport2023.mission`. This will create a folder `parsed/Spaceport2023.mission` which contains the parsed telemetry data for that mission. Note that the `Spaceport2023.mission` sub folder must not exist before running the command.