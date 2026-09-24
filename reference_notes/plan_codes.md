# My Prompt
Hello there. As part of my Research Methodolgy class, we need to perform a research experiment on a Cybersecurity or Forensics Topic.

We were inspired a bit by this attatched PDF to "explore how different filesystems handle data recovery or speed?". The idea on paper was "hey, if we put data on an exteral USB Flash Drive formatted NTFS, wipe the drive and then attempt to recover the data with ddrescue or something, can we do that? And what happens if the drive was formatted with Exfat or EX4 or Brtfs or XFS or something? If we write a bash script that could automate this, we just leave it running for 2 hours and we get our data."


Here's the rough plan we cooked up:


```

    1. In the Downloads folder, create a results.txt
    2. Plug the USB into a computer running an Ubuntu-based OS. Get the bash script to get which /dev/sdx it is and its uuid and remember it. Also log info with SMART or any equivlant on the Benchmark and State of the USB Flash Drive (like the number of failing sectors) so we know the baseline.


    3. On Linux terminal run the “sudo mkfs.ntfs -f /dev/sdx” command to format the USB to ntfs.


    4. We have 2 options here.

Plan A: Fill USB with dummy data (80% to 100% capacity) and a target flag file. The idea is that when we later wipe the USB, we want to see if it's possible to retrieve the flag and if so, how quickly we can on different file systems.

Plan B: Fill USB with dummy data (80% to 100% capacity) with files such as photos. These photos are made up of squares of solid colours. If we go with plan B, we hash the photos beforehand and compare the hashes to the retrieved photos to see if they match. If the hashes are different, we check what changed. Was it a change in the metadata or are the individual pixels different colours because data was overritten there?



    5. Put dummy info onto USB

    6. Use mkfs to either quick format or rm rf to quick delete the contents of the USB. (We haven't decided on which option yet)

Step 7: Depending on what we picked for step 4, do the check for that. Use ddrescue to recover data.

    8. Do steps 2 to 7, X times and write results to results.txt, also include additional information such as recovery speed and recovery rate.
Other file systems (repeat steps 1 to 8):
Ext4
Xfat
Fat32
Brtfs
Xfs


```



My job is to create the basic skeleton of the bash script (so the team knows what the broad goal is), leaving in gaps for the otherteam members to fill in the games.



Here's my rough Bash Psoedocode I'd like you to fill out as much as we can so we can give this incomplete bash script to our team's programmers to fill out the rest:


```

#!/usr/bin/env bash
set -euo pipefail

#Step 0, Set up variables we will need for later.

#We will manually enter uuid of the USB Flash Drive later
uuid=""

#We will manually enter the sdx slot later.
sdx=""

#number of times we want each test to run.
num_of_runs=10

#This is because when we later do automatic mounts and stuff, it would help to make sure we don't target the wrong usb and/or slot.



#Function for step 7. This will make sense later.

def function step_7_ddrescue_times_examamine()

#Step 1: Create Results.txt

touch ~/Downloads/results.txt

#Function to do some prelimary benchmarking and SMART/bad blocks.

def function benchmark_usb -> write output to results.txt


#Function to run for ntfs tests:

def function ntfs_tests(): {

    check if target usb has correct uuid and sdx

    for num in num_of_runs:
        
        #Step 3: format USB to ntfs
        sudo mkfs.ntfs -f /dev/sdx

        #Steps 4 and 5: copy target/dummy data to usb

        sudo mount usb

        sudo cp "path_to_target_or_dummy_data"
        #NOTE: This has to be a placeholder for now until we figure out what we're doing here.


        #Step 6. Either quickformat or rm delete the contents of the USB. Not sure yet which option we're going for so I'll leave in both options in skeleton form albeit commented.


        #If Quick formatting:

        # sudo umount usb ; sudo sudo mkfs.ntfs -f /dev/sdx

        #If quick deleting

        #sudo rm rf data on usb


        #Step 7: Run checks. For this skeleton, assume we're doing the flag strat rather than the photo strat for the same of the example. So back in step 4-5, we filled the USB with junk data and a "flag.txt". We run ddescue and look for flag.txt. If we find it, we record it was found and the time taken. Log it to results.txt

        step_7_ddrescue_times_examamine()

        
 }


ntfs_tests()


#Functions for the other filesystems - Do these later. Lets fill in the ntfs one first.           




```


So yeah, can you help create this skeleton to the best of your ability to help the rest of the team finish it?

# Chat's Answer

Yes. The idea is very workable for a Research Methodology project, and the paper you attached gives you a sensible starting workflow rather than an exact experiment to copy. The paper uses **Gddrescue to create an image and PhotoRec to carve files from that image**, while recording things such as time, sectors accessed, image size, and recovered data.  It explicitly describes Gddrescue as an imaging tool—not the tool that actually reconstructs individual files.  Their second method is essentially `drive → ddrescue image → PhotoRec → recovered files`, which is very close to what you want. 

There are a few things I would change in your design before handing the skeleton to the programmers:

1. **Don't use the filesystem UUID as the permanent USB identifier.** Every `mkfs` can generate a new filesystem UUID. Instead, identify the physical USB using its **serial number + model + capacity**, preferably also its `/dev/disk/by-id/...` path. You can still record each newly generated filesystem UUID in your results.
2. **ddrescue doesn't recover `flag.txt`.** It should make `run01.img`; then PhotoRec or another carving tool scans `run01.img`. Also, PhotoRec often does **not preserve the original filename**, so looking specifically for a file named `flag.txt` is unreliable. Search recovered file *contents* for a unique flag token instead.
3. **Pick either quick-format or deletion as your main experiment.** They answer different questions. `rm` asks, "What remains after file deletion?" Quick formatting asks, "What remains after recreating the filesystem?" If filesystem type is your independent variable, I'd make **quick format your primary condition** and perhaps deletion a separate experiment later.
4. **Plan B is scientifically stronger than one flag file.** Known PNG/JPEG/PDF files plus SHA-256 hashes let you report exact recovery percentages. You can still put a unique flag inside the dataset. I would eventually calculate `exact files recovered / total target files × 100`, rather than merely yes/no flag recovery.

The paper itself found 29.8 GB using direct PhotoRec versus 30.2 GB and 30.8 GB when carving disk images made using Gddrescue/Safecopy, so measuring **amount recovered and recovery time** fits nicely with the type of experimental methodology you're building. 

## A much stronger Bash skeleton

I've deliberately made the dangerous portions fairly defensive. It starts in `DRY_RUN=1`, verifies the physical USB, keeps recovery output **off the experimental USB**, records timings, records the filesystem UUID generated for each trial, and gives your teammates obvious `TODO` sections.

```bash
#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

###############################################################################
# USB FILESYSTEM DATA-RECOVERY EXPERIMENT
#
# PURPOSE:
#   Compare data recoverability after quick-formatting different filesystems.
#
# CURRENT IMPLEMENTATION:
#   NTFS skeleton only.
#
# INTENDED WORKFLOW:
#
#   Verify USB
#       ↓
#   Record hardware/baseline information
#       ↓
#   Format NTFS
#       ↓
#   Mount
#       ↓
#   Fill with experimental data + unique flag
#       ↓
#   Unmount
#       ↓
#   Quick-format NTFS
#       ↓
#   ddrescue -> disk image
#       ↓
#   PhotoRec -> recovered files
#       ↓
#   Search recovered data for unique flag
#       ↓
#   Record result + timings
#
###############################################################################


###############################################################################
# STEP 0 — EXPERIMENT SETTINGS
###############################################################################

# Number of repeated trials per filesystem.
NUM_RUNS=10

# ---------------------------------------------------------------------------
# VERY IMPORTANT:
# Put the experimental USB DEVICE here.
#
# Prefer /dev/disk/by-id/... eventually rather than /dev/sdX.
#
# Example:
# TARGET_DISK="/dev/sdb"
# TARGET_PART="/dev/sdb1"
# ---------------------------------------------------------------------------

TARGET_DISK="/dev/sdX"
TARGET_PART="/dev/sdX1"


# Physical USB identification.
#
# Unlike the filesystem UUID, these should NOT normally change when mkfs runs.
# Fill these in after examining:
#
#   lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN
#
EXPECTED_SERIAL=""
EXPECTED_MODEL=""
EXPECTED_SIZE_BYTES=""


# Mount location for the experimental filesystem.
MOUNT_POINT="/mnt/fs_recovery_test"


# IMPORTANT:
# This MUST be on the COMPUTER'S INTERNAL DRIVE or another separate disk.
# Never recover data back onto the USB being tested.
WORK_ROOT="${HOME}/Downloads/usb_recovery_experiment"

IMAGE_ROOT="${WORK_ROOT}/images"
RECOVERY_ROOT="${WORK_ROOT}/recovered"
LOG_ROOT="${WORK_ROOT}/logs"
CORPUS_ROOT="${WORK_ROOT}/corpus"

RESULTS_FILE="${HOME}/Downloads/results.txt"


# How much of the filesystem should approximately be occupied.
FILL_PERCENT=80


# Experiment condition.
#
# Valid planned values:
#
#   quick_format
#   rm_delete
#
DELETION_MODE="quick_format"


# SAFETY SWITCH.
#
# Leave at 1 while programmers develop/test the script.
#
# Change to 0 ONLY when the USB identity checks have been tested.
DRY_RUN=1


###############################################################################
# GENERIC HELPER FUNCTIONS
###############################################################################

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}


log() {
    local message="$*"
    printf '[%s] %s\n' "$(timestamp)" "$message" | tee -a "$RESULTS_FILE"
}


die() {
    log "FATAL: $*"
    exit 1
}


require_command() {

    local cmd="$1"

    if ! command -v "$cmd" >/dev/null 2>&1; then
        die "Required program is missing: $cmd"
    fi
}


run_destructive() {

    # Wrapper for commands that can modify/destroy USB contents.

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "DRY RUN: $*"
        return 0
    fi

    "$@"
}


elapsed_seconds() {

    # Usage:
    #
    # start=$(date +%s)
    # ...
    # elapsed_seconds "$start"

    local start="$1"
    local end

    end=$(date +%s)

    echo $(( end - start ))
}


###############################################################################
# INITIAL SETUP
###############################################################################

setup_directories() {

    mkdir -p \
        "$WORK_ROOT" \
        "$IMAGE_ROOT" \
        "$RECOVERY_ROOT" \
        "$LOG_ROOT" \
        "$CORPUS_ROOT"

    touch "$RESULTS_FILE"
}


check_dependencies() {

    require_command lsblk
    require_command blkid
    require_command blockdev
    require_command findmnt
    require_command mountpoint
    require_command sha256sum
    require_command ddrescue
    require_command grep
    require_command uuidgen

    # NTFS formatter.
    require_command mkfs.ntfs

    # These are optional at this stage.
    #
    # smartctl
    # photorec
}


###############################################################################
# STEP 2 — IDENTIFY AND VERIFY USB
###############################################################################

verify_target_usb() {

    log "Verifying target USB..."

    if [[ ! -b "$TARGET_DISK" ]]; then
        die "$TARGET_DISK does not exist or is not a block device."
    fi

    if [[ ! -b "$TARGET_PART" ]]; then
        die "$TARGET_PART does not exist or is not a block device."
    fi


    local actual_serial
    local actual_model
    local actual_size

    actual_serial="$(
        lsblk -dn -o SERIAL "$TARGET_DISK" \
        | xargs
    )"

    actual_model="$(
        lsblk -dn -o MODEL "$TARGET_DISK" \
        | xargs
    )"

    actual_size="$(
        blockdev --getsize64 "$TARGET_DISK"
    )"


    log "Target disk:   $TARGET_DISK"
    log "Target part:   $TARGET_PART"
    log "Detected model: $actual_model"
    log "Detected serial: $actual_serial"
    log "Detected size: $actual_size bytes"


    # Only check values that the research team has configured.

    if [[ -n "$EXPECTED_SERIAL" ]]; then

        if [[ "$actual_serial" != "$EXPECTED_SERIAL" ]]; then
            die "USB serial number does not match expected device."
        fi

    fi


    if [[ -n "$EXPECTED_MODEL" ]]; then

        if [[ "$actual_model" != "$EXPECTED_MODEL" ]]; then
            die "USB model does not match expected device."
        fi

    fi


    if [[ -n "$EXPECTED_SIZE_BYTES" ]]; then

        if [[ "$actual_size" != "$EXPECTED_SIZE_BYTES" ]]; then
            die "USB capacity does not match expected device."
        fi

    fi


    log "USB identity checks passed."
}


###############################################################################
# SAFETY: UNMOUNT USB BEFORE FORMATTING/IMAGING
###############################################################################

unmount_target() {

    log "Checking for mounted target partitions..."

    while read -r mounted_device; do

        [[ -z "$mounted_device" ]] && continue

        log "Unmounting $mounted_device"

        run_destructive sudo umount "$mounted_device"

    done < <(
        lsblk -nrpo NAME,MOUNTPOINT "$TARGET_DISK" \
        | awk '$2 != "" {print $1}'
    )
}


###############################################################################
# STEP 2 — BASELINE HARDWARE INFORMATION
###############################################################################

benchmark_usb() {

    log "============================================================"
    log "USB BASELINE INFORMATION"
    log "============================================================"

    {
        echo
        echo "----- lsblk -----"

        lsblk \
            -o NAME,PATH,SIZE,MODEL,SERIAL,TRAN,FSTYPE,UUID,MOUNTPOINTS \
            "$TARGET_DISK"

        echo
        echo "----- blockdev -----"

        echo "Disk size bytes:"
        blockdev --getsize64 "$TARGET_DISK"

        echo
        echo "----- udev -----"

        udevadm info \
            --query=property \
            --name="$TARGET_DISK" \
            2>&1 || true

        echo

    } >> "$RESULTS_FILE"


    ###########################################################################
    # SMART
    #
    # NOTE:
    # Many USB flash drives do NOT expose SMART data.
    # Failure here therefore does not necessarily mean there is a problem.
    ###########################################################################

    if command -v smartctl >/dev/null 2>&1; then

        {
            echo
            echo "----- SMART -----"

            sudo smartctl -a "$TARGET_DISK" 2>&1 \
                || echo "SMART unavailable/not supported through this USB device."

            echo

        } >> "$RESULTS_FILE"

    else

        log "smartctl not installed; SMART baseline skipped."

    fi


    ###########################################################################
    # OPTIONAL READ-ONLY BAD BLOCK TEST
    #
    # The programmers may enable something similar later.
    #
    # DO NOT use:
    #
    #     badblocks -w
    #
    # because that is a destructive write test.
    #
    ###########################################################################

    # sudo badblocks -sv "$TARGET_DISK" \
    #     >> "$RESULTS_FILE" 2>&1


    ###########################################################################
    # OPTIONAL PERFORMANCE BENCHMARK
    #
    # TODO:
    # Team decides whether benchmarking should be included.
    #
    # If included, use the same method before and after the experiment.
    ###########################################################################

    # Example read benchmark only:
    #
    # sudo dd \
    #     if="$TARGET_DISK" \
    #     of=/dev/null \
    #     bs=16M \
    #     count=256 \
    #     iflag=direct \
    #     status=progress

    log "Baseline recording complete."
}


###############################################################################
# STEP 3 — FORMAT NTFS
###############################################################################

format_ntfs() {

    log "Formatting $TARGET_PART as NTFS..."

    unmount_target

    run_destructive \
        sudo mkfs.ntfs -f "$TARGET_PART"

    if [[ "$DRY_RUN" -eq 0 ]]; then

        sudo udevadm settle

        local new_uuid

        new_uuid="$(
            blkid \
                -s UUID \
                -o value \
                "$TARGET_PART" \
                2>/dev/null || true
        )"

        log "New NTFS filesystem UUID: $new_uuid"

    fi
}


###############################################################################
# MOUNT EXPERIMENTAL FILESYSTEM
###############################################################################

mount_target() {

    log "Mounting experimental filesystem..."

    sudo mkdir -p "$MOUNT_POINT"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        log "DRY RUN: sudo mount $TARGET_PART $MOUNT_POINT"
        return 0
    fi

    sudo mount "$TARGET_PART" "$MOUNT_POINT"

    if ! mountpoint -q "$MOUNT_POINT"; then
        die "Target filesystem failed to mount."
    fi
}


###############################################################################
# STEP 4 — PREPARE UNIQUE DATA FOR EACH RUN
###############################################################################

create_run_corpus() {

    local filesystem="$1"
    local run_number="$2"

    local run_corpus
    local flag_token

    run_corpus="${CORPUS_ROOT}/${filesystem}_run_${run_number}"

    rm -rf "$run_corpus"
    mkdir -p "$run_corpus"


    ###########################################################################
    # UNIQUE FLAG
    #
    # We use a DIFFERENT token for every trial.
    #
    # This prevents a flag left behind by an earlier experiment from being
    # falsely counted as a successful recovery during a later experiment.
    ###########################################################################

    flag_token="$(
        printf 'CYBERFORENSICS_%s_RUN_%02d_%s' \
            "$filesystem" \
            "$run_number" \
            "$(uuidgen)"
    )"


    printf '%s\n' "$flag_token" \
        > "${run_corpus}/flag.txt"


    ###########################################################################
    # TODO — REAL TEST CORPUS
    #
    # Eventually replace/expand this with:
    #
    #   target JPEG files
    #   target PNG files
    #   target PDF files
    #   possibly DOCX/ZIP/etc.
    #
    # Prefer a STANDARDIZED corpus that is identical between filesystems.
    #
    ###########################################################################


    ###########################################################################
    # Create hash manifest.
    ###########################################################################

    (
        cd "$run_corpus"

        find . \
            -type f \
            ! -name 'manifest.sha256' \
            -print0 \
        | sort -z \
        | xargs -0 sha256sum

    ) > "${run_corpus}/manifest.sha256"


    # Return flag token to caller.
    echo "$flag_token"
}


###############################################################################
# STEPS 4–5 — COPY EXPERIMENTAL DATA TO USB
###############################################################################

populate_usb() {

    local filesystem="$1"
    local run_number="$2"

    local run_corpus

    run_corpus="${CORPUS_ROOT}/${filesystem}_run_${run_number}"


    log "Copying target experimental files to USB."


    if [[ "$DRY_RUN" -eq 1 ]]; then

        log "DRY RUN: copy $run_corpus to $MOUNT_POINT"

        return 0

    fi


    sudo cp -a \
        "${run_corpus}/." \
        "${MOUNT_POINT}/"


    ###########################################################################
    # TODO — FILL DRIVE TO APPROXIMATELY 80%
    #
    # Do NOT simply create one giant >4 GiB file if FAT32 will eventually
    # be tested, because FAT32 cannot store individual files larger than 4 GiB.
    #
    # Better approach:
    #
    #   determine desired number of bytes
    #   create many 512 MiB / 1 GiB filler files
    #   stop when desired utilization is reached
    #
    # Filler should be generated the SAME WAY for every filesystem.
    ###########################################################################

    # Example placeholder only:
    #
    # while filesystem_usage < FILL_PERCENT:
    #
    #     dd if=/dev/zero \
    #        of="$MOUNT_POINT/filler_XXXX.bin" \
    #        bs=1M \
    #        count=1024 \
    #        conv=fsync
    #
    # done


    sync

    log "Experimental data copied."
}


###############################################################################
# RECORD FILESYSTEM STATE BEFORE DELETION/FORMAT
###############################################################################

record_pre_deletion_state() {

    local filesystem="$1"
    local run_number="$2"

    local uuid

    uuid="$(
        blkid \
            -s UUID \
            -o value \
            "$TARGET_PART" \
            2>/dev/null || true
    )"

    log "PRE-DELETION fs=$filesystem run=$run_number UUID=$uuid"


    {
        echo
        echo "----- PRE-DELETION FILESYSTEM -----"
        echo "Filesystem: $filesystem"
        echo "Run: $run_number"
        echo "UUID: $uuid"

        df -h "$MOUNT_POINT" 2>&1 || true

        echo

    } >> "$RESULTS_FILE"
}


###############################################################################
# STEP 6A — QUICK FORMAT
###############################################################################

quick_format_ntfs() {

    log "Performing NTFS quick format."

    unmount_target

    run_destructive \
        sudo mkfs.ntfs -f "$TARGET_PART"

    if [[ "$DRY_RUN" -eq 0 ]]; then
        sudo udevadm settle
    fi
}


###############################################################################
# STEP 6B — DELETE FILES
###############################################################################

delete_files_only() {

    log "Deleting filesystem contents."

    if [[ "$DRY_RUN" -eq 1 ]]; then

        log "DRY RUN: delete contents of $MOUNT_POINT"

        return 0

    fi


    ###########################################################################
    # IMPORTANT SAFETY CHECK
    #
    # Never perform recursive deletion unless the expected USB is REALLY
    # mounted here.
    ###########################################################################

    if ! mountpoint -q "$MOUNT_POINT"; then
        die "$MOUNT_POINT is not mounted. Refusing deletion."
    fi


    # Safer than:
    #
    #     rm -rf "$MOUNT_POINT"/*
    #
    # -xdev prevents traversal into another filesystem.

    sudo find "$MOUNT_POINT" \
        -xdev \
        -mindepth 1 \
        -delete


    sync

    unmount_target
}


###############################################################################
# STEP 7A — CREATE FORENSIC IMAGE USING DDRESCUE
###############################################################################

create_ddrescue_image() {

    local filesystem="$1"
    local run_number="$2"

    local image_file
    local map_file
    local ddrescue_log

    image_file="${IMAGE_ROOT}/${filesystem}_run_${run_number}.img"
    map_file="${LOG_ROOT}/${filesystem}_run_${run_number}.map"
    ddrescue_log="${LOG_ROOT}/${filesystem}_run_${run_number}_ddrescue.log"


    log "Creating disk image with ddrescue."
    log "Source: $TARGET_PART"
    log "Image:  $image_file"


    unmount_target


    if [[ "$DRY_RUN" -eq 1 ]]; then

        log "DRY RUN: sudo ddrescue -f -n $TARGET_PART $image_file $map_file"

        echo "0"

        return 0
    fi


    rm -f "$image_file" "$map_file" "$ddrescue_log"


    local start_time
    local end_time
    local duration

    start_time=$(date +%s)


    ###########################################################################
    # -n:
    #   First pass without retrying bad sectors repeatedly.
    #
    # Team can decide whether additional passes should be included later.
    ###########################################################################

    if sudo ddrescue \
        -f \
        -n \
        "$TARGET_PART" \
        "$image_file" \
        "$map_file" \
        2>&1 | tee "$ddrescue_log"
    then

        log "ddrescue completed successfully."

    else

        log "WARNING: ddrescue returned a non-zero exit status."

    fi


    end_time=$(date +%s)

    duration=$(( end_time - start_time ))

    log "ddrescue duration: ${duration} seconds"

    echo "$duration"
}


###############################################################################
# STEP 7B — FILE CARVING
###############################################################################

carve_image_with_photorec() {

    local filesystem="$1"
    local run_number="$2"

    local image_file
    local recovered_dir

    image_file="${IMAGE_ROOT}/${filesystem}_run_${run_number}.img"
    recovered_dir="${RECOVERY_ROOT}/${filesystem}_run_${run_number}"


    mkdir -p "$recovered_dir"


    log "Starting file carving."
    log "Image: $image_file"
    log "Output: $recovered_dir"


    local start_time
    local end_time
    local duration

    start_time=$(date +%s)


    ###########################################################################
    # TODO — TEAM PROGRAMMER SECTION
    #
    # PhotoRec should be configured here for NON-INTERACTIVE operation.
    #
    # IMPORTANT:
    #
    # The recovery SOURCE should be:
    #
    #     $image_file
    #
    # The output should be:
    #
    #     $recovered_dir
    #
    # Do NOT recover files onto the experimental USB.
    #
    #
    # The exact PhotoRec command will depend upon:
    #
    #   - which file formats the experiment includes
    #   - whether the entire image or filesystem area is scanned
    #   - PhotoRec command-mode options
    #
    #
    # During early development, the team can manually verify PhotoRec settings
    # before automating them.
    ###########################################################################


    if [[ "$DRY_RUN" -eq 1 ]]; then

        log "DRY RUN: PhotoRec would scan $image_file"

    else

        #######################################################################
        # TODO:
        #
        # photorec [AUTOMATED ARGUMENTS HERE]
        #
        #######################################################################

        log "TODO: PhotoRec automation has not yet been implemented."

    fi


    end_time=$(date +%s)

    duration=$(( end_time - start_time ))

    log "File carving duration: ${duration} seconds"

    echo "$duration"
}


###############################################################################
# STEP 7C — EXAMINE RECOVERED DATA
###############################################################################

examine_recovered_data() {

    local filesystem="$1"
    local run_number="$2"
    local flag_token="$3"

    local recovered_dir

    recovered_dir="${RECOVERY_ROOT}/${filesystem}_run_${run_number}"


    log "Searching recovered files for unique flag token."


    ###########################################################################
    # IMPORTANT:
    #
    # Do NOT look for a recovered file named "flag.txt".
    #
    # Carving tools commonly assign new filenames.
    #
    # Instead, search recovered CONTENT for the unique token.
    ###########################################################################

    local found="NO"
    local match=""


    if [[ -d "$recovered_dir" ]]; then

        match="$(
            grep \
                -R \
                -a \
                -l \
                -F \
                -- "$flag_token" \
                "$recovered_dir" \
                2>/dev/null \
            | head -n 1 \
            || true
        )"


        if [[ -n "$match" ]]; then
            found="YES"
        fi

    fi


    local recovered_file_count="0"
    local recovered_bytes="0"


    if [[ -d "$recovered_dir" ]]; then

        recovered_file_count="$(
            find "$recovered_dir" \
                -type f \
                | wc -l
        )"

        recovered_bytes="$(
            du \
                -sb \
                "$recovered_dir" \
                2>/dev/null \
                | awk '{print $1}'
        )"

    fi


    log "Flag recovered: $found"
    log "Recovered files: $recovered_file_count"
    log "Recovered bytes: $recovered_bytes"

    if [[ "$found" == "YES" ]]; then
        log "Flag discovered in: $match"
    fi


    ###########################################################################
    # Return machine-readable values.
    ###########################################################################

    printf '%s|%s|%s\n' \
        "$found" \
        "$recovered_file_count" \
        "$recovered_bytes"
}


###############################################################################
# STEP 7 — COMPLETE RECOVERY/EXAMINATION WORKFLOW
###############################################################################

step_7_ddrescue_time_examine() {

    local filesystem="$1"
    local run_number="$2"
    local flag_token="$3"

    local ddrescue_seconds
    local carving_seconds
    local examination_result


    ddrescue_seconds="$(
        create_ddrescue_image \
            "$filesystem" \
            "$run_number"
    )"


    carving_seconds="$(
        carve_image_with_photorec \
            "$filesystem" \
            "$run_number"
    )"


    examination_result="$(
        examine_recovered_data \
            "$filesystem" \
            "$run_number" \
            "$flag_token"
    )"


    log "STEP 7 COMPLETE"
    log "ddrescue_seconds=$ddrescue_seconds"
    log "carving_seconds=$carving_seconds"
    log "recovery_result=$examination_result"
}


###############################################################################
# RECORD RUN SUMMARY
###############################################################################

record_run_summary() {

    local filesystem="$1"
    local run_number="$2"

    log "------------------------------------------------------------"
    log "RUN COMPLETE"
    log "filesystem=$filesystem"
    log "run=$run_number"
    log "deletion_mode=$DELETION_MODE"
    log "------------------------------------------------------------"
}


###############################################################################
# CLEANUP BETWEEN RUNS
###############################################################################

cleanup_run() {

    local filesystem="$1"
    local run_number="$2"


    ###########################################################################
    # TODO:
    #
    # Decide whether disk images should be retained.
    #
    # Keeping ten complete USB images for every filesystem could consume a
    # HUGE amount of storage.
    #
    # Example:
    #
    # 64 GB USB
    # × 10 trials
    # × 6 filesystems
    # = ~3.84 TB of image files alone.
    #
    # A practical approach is:
    #
    #   1. acquire image
    #   2. carve it
    #   3. record results/hashes
    #   4. delete the image
    #
    ###########################################################################

    # rm -f \
    #     "${IMAGE_ROOT}/${filesystem}_run_${run_number}.img"

    :
}


###############################################################################
# NTFS EXPERIMENT
###############################################################################

ntfs_tests() {

    local filesystem="ntfs"


    log "============================================================"
    log "STARTING NTFS EXPERIMENT"
    log "NUMBER OF RUNS: $NUM_RUNS"
    log "============================================================"


    verify_target_usb


    for (( run_number=1;
           run_number<=NUM_RUNS;
           run_number++ ))
    do

        log "============================================================"
        log "NTFS RUN $run_number OF $NUM_RUNS"
        log "============================================================"


        #######################################################################
        # STEP 3 — CREATE NTFS FILESYSTEM
        #######################################################################

        format_ntfs


        #######################################################################
        # MOUNT IT
        #######################################################################

        mount_target


        #######################################################################
        # STEP 4 — CREATE THIS RUN'S UNIQUE CORPUS
        #######################################################################

        flag_token="$(
            create_run_corpus \
                "$filesystem" \
                "$run_number"
        )"


        log "Unique flag token generated for this run."


        #######################################################################
        # STEP 5 — WRITE EXPERIMENTAL DATA
        #######################################################################

        populate_usb \
            "$filesystem" \
            "$run_number"


        record_pre_deletion_state \
            "$filesystem" \
            "$run_number"


        #######################################################################
        # STEP 6 — DESTROY FILESYSTEM INFORMATION
        #######################################################################

        case "$DELETION_MODE" in

            quick_format)

                quick_format_ntfs
                ;;

            rm_delete)

                delete_files_only
                ;;

            *)

                die "Unknown DELETION_MODE: $DELETION_MODE"
                ;;

        esac


        #######################################################################
        # STEP 7 — IMAGE, CARVE, EXAMINE
        #######################################################################

        step_7_ddrescue_time_examine \
            "$filesystem" \
            "$run_number" \
            "$flag_token"


        #######################################################################
        # STEP 8 — RECORD RESULT
        #######################################################################

        record_run_summary \
            "$filesystem" \
            "$run_number"


        cleanup_run \
            "$filesystem" \
            "$run_number"

    done


    log "NTFS testing complete."
}


###############################################################################
# FUTURE FILESYSTEM FUNCTIONS
###############################################################################

ext4_tests() {

    ###########################################################################
    # TODO
    #
    # Same experimental procedure as NTFS, except:
    #
    #     mkfs.ext4 "$TARGET_PART"
    #
    # Everything else should ideally stay IDENTICAL.
    ###########################################################################

    :
}


exfat_tests() {

    ###########################################################################
    # TODO
    #
    #     mkfs.exfat "$TARGET_PART"
    ###########################################################################

    :
}


fat32_tests() {

    ###########################################################################
    # TODO
    #
    # Usually:
    #
    #     mkfs.vfat -F 32 "$TARGET_PART"
    #
    # Remember:
    # FAT32 individual file-size limit must be considered when making filler.
    ###########################################################################

    :
}


btrfs_tests() {

    ###########################################################################
    # TODO
    #
    #     mkfs.btrfs -f "$TARGET_PART"
    ###########################################################################

    :
}


xfs_tests() {

    ###########################################################################
    # TODO
    #
    #     mkfs.xfs -f "$TARGET_PART"
    ###########################################################################

    :
}


###############################################################################
# MAIN
###############################################################################

main() {

    setup_directories

    check_dependencies

    log ""
    log "############################################################"
    log "FILESYSTEM RECOVERY EXPERIMENT STARTED"
    log "############################################################"

    log "DRY_RUN=$DRY_RUN"
    log "TARGET_DISK=$TARGET_DISK"
    log "TARGET_PART=$TARGET_PART"
    log "DELETION_MODE=$DELETION_MODE"
    log "NUM_RUNS=$NUM_RUNS"


    ###########################################################################
    # ONE-TIME USB BASELINE
    ###########################################################################

    verify_target_usb

    benchmark_usb


    ###########################################################################
    # RUN EXPERIMENTS
    ###########################################################################

    ntfs_tests

    # Later:
    #
    # ext4_tests
    # exfat_tests
    # fat32_tests
    # btrfs_tests
    # xfs_tests


    log "############################################################"
    log "EXPERIMENT FINISHED"
    log "############################################################"
}


main "$@"
```

### A few particularly important decisions behind this version

Your original pseudocode had this idea:

```bash
uuid=""
sdx=""
```

I would change that. **`sdx` itself is also not guaranteed to remain stable.** Today the flash drive may be `/dev/sdb`; tomorrow, because another disk was plugged in first, it might be `/dev/sdc`. Eventually I would configure the script with something like:

```bash
TARGET_DISK="/dev/disk/by-id/usb-SanDisk_Ultra_1234567890-0:0"
```

and then independently verify serial/model/capacity. That makes an accidental format of someone's internal SSD dramatically less likely.

There is also an important conceptual correction to:

```text
Use ddrescue to recover data.
```

The pipeline should really be:

```text
USB partition
      │
      ▼
   ddrescue
      │
      ▼
 run01.img
      │
      ▼
   PhotoRec
      │
      ▼
recovered files
      │
      ▼
hash / flag examination
```

That's essentially the workflow in the paper's Figure 2 on page 3: disk → disk imaging → disk image → file carving → recovered data. 

And I particularly like the idea of storing the **ddrescue `.map` file** for every experiment. The paper notes that ddrescue maintains a log/map that allows the operation to be resumed and records its progress through problematic areas.  That gives you extra experimental evidence besides just "we got the file back."

### One methodological issue I would solve before your team starts coding

I'd actually shrink the test area.

Suppose it's a 64 GB flash drive:

```text
64 GB × 10 repetitions × 6 filesystems
≈ 3.84 TB read just for first-pass imaging
```

Then you're writing roughly 80% of it before every trial as well. That's a *lot* of unnecessary runtime and flash writes for a class experiment.

I'd seriously consider making the experimental partition something like **4–8 GiB**, while leaving the rest of the USB unused. You can still fill the test filesystem to 80%, perform exactly the same format/recovery operation, and finish 60 runs in a remotely sane amount of time.

That also gives you the opportunity to **zero the experimental partition between trials** so run 7 doesn't contain old remnants from runs 1–6. Otherwise, PhotoRec could recover garbage from earlier experiments and make your "total recovered data" statistic misleading.

For example, between experiments your eventual reset function might deliberately do something along the lines of:

```bash
sudo dd if=/dev/zero \
    of="$TARGET_PART" \
    bs=16M \
    status=progress \
    conv=fsync
```

**before** creating the next filesystem. I would not silently put that into the current script yet, because your group should agree that a full logical reset is part of the methodology.

### I would also lean toward Plan B

Instead of:

```text
Did we recover FLAG.txt?
YES / NO
```

imagine your corpus contains 100 known files:

```text
20 PNG
20 JPEG
20 PDF
20 TXT
20 ZIP
```

Before copying them:

```bash
find corpus -type f -print0 |
    sort -z |
    xargs -0 sha256sum > manifest.sha256
```

After PhotoRec:

```text
Original files:                    100
Files recovered with exact hash:   83
Files recovered but corrupted:       6
Not recovered:                      11
Exact recovery rate:               83%
Total bytes recovered:             ...
ddrescue imaging time:              ...
PhotoRec carving time:              ...
```

That starts looking like a genuinely nice quantitative cybersecurity/forensics experiment rather than simply a scripting demonstration.

And the solid-colour image idea you mentioned can make the corrupted-file cases visually interesting: **SHA-256 tells you immediately that something changed**, while image comparison can tell you *how* it changed.

The next piece I'd build with your programmers is the **`populate_usb()` function**, because getting every filesystem to *exactly the same occupancy percentage with exactly the same corpus* is probably the biggest thing you need to standardize before touching PhotoRec automation.


## Gemini's Answer

This bash skeleton structures the automation for formatting, data staging, wiping, and recovery timing across your selected file systems.

Based on the attached research, GNU `ddrescue` is a low-level disk imaging tool designed to copy data block-by-block and handle faulty sectors, rather than a direct file extraction tool. To successfully retrieve your `flag.txt` or photo files after wiping the drive, the script is designed to first create a disk image with `ddrescue`, which can then be parsed by a file carving tool like `PhotoRec`. This two-step process—imaging the drive first, then carving the image—has been shown to safely yield significantly higher data recovery rates than carving the drive directly.

```bash
#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# STEP 0: Configuration & Variables
# ==========================================

# WARNING: Double-check these before running!
TARGET_UUID="your-usb-uuid-here" 
TARGET_DEV="/dev/sdx"           

NUM_OF_RUNS=10
RESULTS_FILE="$HOME/Downloads/results.txt"
MOUNT_POINT="/mnt/usb_test"
FLAG_FILE_NAME="flag.txt"
DUMMY_DATA_DIR="$HOME/Downloads/dummy_data" # Path to your 80% capacity junk data

# ==========================================
# STEP 1: Initialize Results Log
# ==========================================

mkdir -p "$HOME/Downloads"
touch "$RESULTS_FILE"
echo "=== File System Recovery Benchmark Started: $(date) ===" >> "$RESULTS_FILE"

# ==========================================
# STEP 2: Baseline Benchmark & SMART Status
# ==========================================

benchmark_usb() {
    echo -e "\n--- Pre-Test SMART Data & Benchmarks for $TARGET_DEV ---" >> "$RESULTS_FILE"
    
    # Log SMART data (requires smartmontools)
    sudo smartctl -a "$TARGET_DEV" >> "$RESULTS_FILE" 2>&1 || echo "SMART not supported on this USB" >> "$RESULTS_FILE"
    
    # Read-only bad blocks check to establish baseline health
    sudo badblocks -v "$TARGET_DEV" >> "$RESULTS_FILE" 2>&1 || true
}

# ==========================================
# STEP 7: Recovery & Examination
# ==========================================

run_recovery_and_examine() {
    local fs_type=$1
    local run_num=$2
    local image_file="$HOME/Downloads/usb_image_${fs_type}_${run_num}.img"
    local map_file="$HOME/Downloads/usb_image_${fs_type}_${run_num}.map"
    local recovered_dir="$HOME/Downloads/recovered_${fs_type}_${run_num}"

    echo "  -> Starting ddrescue imaging for $fs_type (Run $run_num)..." >> "$RESULTS_FILE"
    start_time=$(date +%s)

    # ddrescue creates a raw 1:1 image of the USB
    sudo ddrescue -d -r1 "$TARGET_DEV" "$image_file" "$map_file" >> "$RESULTS_FILE" 2>&1

    end_time_imaging=$(date +%s)
    echo "  -> ddrescue imaging completed in $((end_time_imaging - start_time)) seconds." >> "$RESULTS_FILE"

    # Carving step: Searching the raw image for the flag
    mkdir -p "$recovered_dir"
    echo "  -> Starting PhotoRec carving on the disk image..." >> "$RESULTS_FILE"
    
    # PhotoRec CLI command (searches the .img file, recovers to $recovered_dir)
    sudo photorec /d "$recovered_dir" /cmd "$image_file" search >> "$RESULTS_FILE" 2>&1

    end_time_carving=$(date +%s)
    echo "  -> PhotoRec carving completed in $((end_time_carving - end_time_imaging)) seconds." >> "$RESULTS_FILE"
    
    # Verify if flag.txt was recovered
    if find "$recovered_dir" -type f -name "*$FLAG_FILE_NAME*" | grep -q .; then
        echo "  [SUCCESS] $FLAG_FILE_NAME recovered on $fs_type run $run_num." >> "$RESULTS_FILE"
    else
        echo "  [FAILURE] $FLAG_FILE_NAME NOT recovered on $fs_type run $run_num." >> "$RESULTS_FILE"
    fi

    # Cleanup large image files if storage space is a concern
    # rm "$image_file" "$map_file"
}

# ==========================================
# FILESYSTEM TEST FUNCTIONS
# ==========================================

ntfs_tests() {
    echo -e "\n=== Starting NTFS Tests ===" >> "$RESULTS_FILE"
    
    # Safety Check: Ensure the drive matches our expected UUID (or at least prompt)
    current_uuid=$(sudo blkid -s UUID -o value "$TARGET_DEV" || true)
    if [ "$current_uuid" != "$TARGET_UUID" ] && [ -n "$current_uuid" ]; then
        echo "Warning: Target device UUID does not match expected UUID. Aborting to prevent accidental data loss."
        exit 1
    fi

    sudo mkdir -p "$MOUNT_POINT"

    for (( i=1; i<=NUM_OF_RUNS; i++ )); do
        echo "- NTFS Run $i -" >> "$RESULTS_FILE"

        # Step 3: Format to NTFS
        sudo mkfs.ntfs -f -q "$TARGET_DEV"

        # Steps 4 & 5: Mount and stage data
        sudo mount "$TARGET_DEV" "$MOUNT_POINT"
        
        # Write dummy data and flag
        # sudo cp -r "$DUMMY_DATA_DIR/"* "$MOUNT_POINT/"
        echo "This is the target flag data for recovery" | sudo tee "$MOUNT_POINT/$FLAG_FILE_NAME" > /dev/null
        
        # Ensure data is written to disk before unmounting
        sync 
        sudo umount "$MOUNT_POINT"

        # Step 6: Wipe Data
        # Option A: Quick Format
        sudo mkfs.ntfs -f -q "$TARGET_DEV"
        
        # Option B: RM Delete (Comment out Option A and uncomment below to use this)
        # sudo mount "$TARGET_DEV" "$MOUNT_POINT"
        # sudo rm -rf "$MOUNT_POINT/"*
        # sync
        # sudo umount "$MOUNT_POINT"

        # Step 7: Recover Data
        run_recovery_and_examine "ntfs" "$i"
    done
}

ext4_tests() {
    echo -e "\n=== Starting Ext4 Tests ===" >> "$RESULTS_FILE"
    # To implement: Use sudo mkfs.ext4 -F "$TARGET_DEV"
    # Copy the loop logic from ntfs_tests
}

exfat_tests() {
    echo -e "\n=== Starting exFAT Tests ===" >> "$RESULTS_FILE"
    # To implement: Use sudo mkfs.exfat "$TARGET_DEV"
}

fat32_tests() {
    echo -e "\n=== Starting FAT32 Tests ===" >> "$RESULTS_FILE"
    # To implement: Use sudo mkfs.vfat -F 32 "$TARGET_DEV"
}

btrfs_tests() {
    echo -e "\n=== Starting Btrfs Tests ===" >> "$RESULTS_FILE"
    # To implement: Use sudo mkfs.btrfs -f "$TARGET_DEV"
}

xfs_tests() {
    echo -e "\n=== Starting XFS Tests ===" >> "$RESULTS_FILE"
    # To implement: Use sudo mkfs.xfs -f "$TARGET_DEV"
}

# ==========================================
# MAIN EXECUTION
# ==========================================

# benchmark_usb
ntfs_tests
# ext4_tests
# exfat_tests
# fat32_tests
# btrfs_tests
# xfs_tests

echo "=== Benchmark Complete ===" >> "$RESULTS_FILE"

```

Have you and your team decided whether you want to proceed with Plan A (the simple flag file) or Plan B (the hex/hash verification of photos) for the final experiment?

# Claude's Answer:

Good research question — file carving robustness varies a lot by filesystem (journaling behavior, metadata layout, whether "deleted" blocks get zeroed on quick-format, etc.), so this is a solid experiment design. I filled out the skeleton with your requested structure, but made one structural change worth flagging: instead of copy-pasting the mkfs/copy/wipe/recover loop six times, I wrote it once as a generic `run_fs_test()` and made `ntfs_tests()`, `ext4_tests()`, etc. thin one-line wrappers around it. Same shape you asked for, way less duplication for your team to keep in sync.

I left the genuinely undecided things as `TODO(team)` stubs (Plan A vs B, format-vs-rm wipe, photo generation/hashing), and implemented the plumbing around them (device verification, benchmarking, ddrescue timing, results logging) since those are less "team decision" and more "someone has to write it once."Passes `bash -n` syntax check. A few things worth flagging to the team before they start filling in the gaps:

- **`verify_target()`** prompts for interactive confirmation (drive serial + device path) before any destructive command runs — this is the thing standing between "wipe the test USB" and "wipe someone's actual disk." Don't strip it out for the unattended run; if you want it fully hands-off, hardcode an `EXPECTED_SERIAL` check instead of the prompt.
- **Marker file lives on the host**, not the USB (`${WORK_DIR}/current_marker.txt`), so it survives the wipe and `step_7` can grep the recovered image for it.
- **Plan B (photos) is a stub** with the hashing/pixel-vs-metadata approach outlined in comments — that's the piece I'd want a human decision on before writing, since "did the pixels change or just the metadata" needs you to pick a concrete diffing method (ImageMagick `compare` vs. re-hashing raw pixel buffers vs. `exiftool` diff).
- **Partition vs. whole-device mounting** is guessed with a fallback (`${dev}1` then `${dev}`) — worth confirming once you know how your `mkfs` commands actually lay things out.
- The `sudo -v` keepalive loop is there so a 2-hour unattended run doesn't stall on a password prompt at minute 15.

One thing to sanity-check with your instructor: NTFS/ext4/Btrfs/XFS are journaling filesystems with pretty different "quick format" semantics (some barely touch data blocks, some zero more than you'd expect), so it's worth deciding now whether "quick format" means the same `mkfs` flags across all six, or you're intentionally comparing each fs's *default* quick-format behavior.

```bash
#!/usr/bin/env bash
#
# fs_recovery_experiment.sh
#
# Compares file-carving / data-recovery outcomes across filesystems
# (NTFS, ext4, exFAT, FAT32, Btrfs, XFS) on a single test USB drive.
# Inspired by the PhotoRec/ddrescue/safecopy methodology in
# "Comparison between File Carving from Disk Drive and Disk Image..."
#
# STATUS: SKELETON. Search for "TODO(team)" for the parts that still
# need a decision or implementation from the rest of the group.
#
# SAFETY:
#   This script runs *destructive* commands (mkfs, rm -rf, ddrescue
#   writing images) against a raw block device. verify_target() exists
#   specifically to stop it from ever touching the wrong disk -- do not
#   remove it, and do not run this against anything but the dedicated
#   test USB.
#
# REQUIRED PACKAGES (Ubuntu/Debian):
#   sudo apt install ntfs-3g dosfstools exfatprogs btrfs-progs xfsprogs \
#                     gddrescue smartmontools hdparm util-linux
#
# USAGE:
#   1. Fill in TARGET_UUID / TARGET_SDX below (or export them before
#      running).
#   2. Decide TEST_STRATEGY and WIPE_METHOD.
#   3. chmod +x fs_recovery_experiment.sh && ./fs_recovery_experiment.sh
#
set -euo pipefail

########################################
# 0. CONFIG -- fill these in before running
########################################

# TODO(team): set once you know which device node + UUID correspond to
# the test USB. Script refuses to run if either is blank.
TARGET_UUID="${TARGET_UUID:-}"
TARGET_SDX="${TARGET_SDX:-}"          # e.g. "sdb"  -- NOT "/dev/sdb"

# How many times to repeat the full format -> fill -> wipe -> recover
# cycle for EACH filesystem.
NUM_RUNS="${NUM_RUNS:-10}"

RESULTS_FILE="${HOME}/Downloads/results.txt"
WORK_DIR="${HOME}/fs_experiment_work"     # scratch space on the HOST disk, not the USB
IMAGE_DIR="${WORK_DIR}/images"            # ddrescue images land here
MOUNT_POINT="/mnt/usb_test"

# Plan A ("flag") vs Plan B ("photo") -- see create_dummy_data() below.
# TODO(team): decide, or run both by looping the whole script twice
# with TEST_STRATEGY set differently each time.
TEST_STRATEGY="${TEST_STRATEGY:-flag}"
FLAG_FILE_NAME="flag.txt"

# "format" = quick mkfs over the top (metadata wiped, data blocks may
#            survive -> this is the classic "carving" scenario).
# "rm"     = mount + rm -rf contents (filesystem stays, files unlinked).
# TODO(team): pick one. You could also run the whole experiment twice,
# once per method, to compare -- the CSV column below already records
# which method was used per row so results won't get mixed up.
WIPE_METHOD="${WIPE_METHOD:-format}"

# How full to fill the drive before wiping (percent).
FILL_TARGET_PERCENT=90

# name:mkfs-command-template pairs. {DEV} is substituted with /dev/$TARGET_SDX.
# Adjust flags to taste (e.g. add -L LABEL, cluster size, etc.)
FILESYSTEMS=(
  "ntfs:mkfs.ntfs -f {DEV}"
  "ext4:mkfs.ext4 -F {DEV}"
  "exfat:mkfs.exfat {DEV}"
  "fat32:mkfs.vfat -F 32 {DEV}"
  "btrfs:mkfs.btrfs -f {DEV}"
  "xfs:mkfs.xfs -f {DEV}"
)

########################################
# 1. Logging / results.txt helpers
########################################

# Human-readable log lines go to results.txt prefixed with "# " so the
# CSV data rows (written elsewhere) stay easy to grep/parse later, e.g.:
#   grep -v '^#' results.txt | column -s, -t
log() {
  local ts
  ts=$(date -u +"%FT%TZ")
  echo "# [${ts}] $*" | tee -a "${RESULTS_FILE}" >&2
}

init_results_file() {
  mkdir -p "$(dirname "${RESULTS_FILE}")"
  touch "${RESULTS_FILE}"
  if ! grep -q '^fs,run,wipe_method' "${RESULTS_FILE}" 2>/dev/null; then
    echo "fs,run,wipe_method,strategy,elapsed_s,image_bytes,flag_found" >> "${RESULTS_FILE}"
  fi
}

########################################
# 2. Safety: make sure we have the right device
########################################

verify_target() {
  if [ -z "${TARGET_UUID}" ] || [ -z "${TARGET_SDX}" ]; then
    echo "ERROR: TARGET_UUID and TARGET_SDX must both be set. Aborting." >&2
    exit 1
  fi

  local dev="/dev/${TARGET_SDX}"
  if [ ! -b "${dev}" ]; then
    echo "ERROR: ${dev} is not a block device. Check TARGET_SDX." >&2
    exit 1
  fi

  # NOTE: the UUID changes every time the drive is reformatted, so this
  # only meaningfully checks against whatever filesystem is on it right
  # now (e.g. however it shipped / was last left). After the first
  # mkfs it's out of date -- we fall back to the device serial number,
  # which doesn't change, as the real safety net.
  local actual_uuid serial
  actual_uuid=$(lsblk -no UUID "${dev}" 2>/dev/null | head -1 || true)
  serial=$(udevadm info --query=property --name="${dev}" 2>/dev/null \
            | grep -oP '(?<=ID_SERIAL=).*' || true)

  log "Target check: dev=${dev} expected_uuid=${TARGET_UUID} actual_uuid=${actual_uuid:-<none>} serial=${serial:-<unknown>}"

  # TODO(team): once you've confirmed the serial the first time, consider
  # hardcoding EXPECTED_SERIAL above and failing automatically instead of
  # prompting -- useful once this runs unattended overnight.
  read -r -p "Confirm this is the correct test USB (${dev}, serial=${serial:-unknown})? Type YES to continue: " confirm
  if [ "${confirm}" != "YES" ]; then
    echo "Aborting: target device not confirmed." >&2
    exit 1
  fi
}

# Keep the cached sudo credential alive for the whole (potentially
# hours-long) run, so it doesn't stall on a password prompt at 2am.
keep_sudo_alive() {
  sudo -v
  ( while true; do sudo -n true; sleep 60; kill -0 "$$" 2>/dev/null || exit; done ) &
  SUDO_KEEPALIVE_PID=$!
}

########################################
# 3. Baseline benchmark (run once, before any filesystem is touched)
########################################

benchmark_usb() {
  local dev="/dev/${TARGET_SDX}"
  log "Benchmarking ${dev} (baseline, before any tests)"

  {
    echo "# --- smartctl -a ---"
    sudo smartctl -a "${dev}" 2>&1 \
      || sudo smartctl -a -d sat "${dev}" 2>&1 \
      || echo "# smartctl unsupported/failed on this device"

    echo "# --- hdparm read speed ---"
    sudo hdparm -tT "${dev}" 2>&1 || echo "# hdparm failed"

    # TODO(team): badblocks -sv is a thorough non-destructive read-only
    # bad-sector scan, but can take a long time on larger drives. Turn
    # on if the time budget allows:
    # echo "# --- badblocks (read-only) ---"
    # sudo badblocks -sv "${dev}" 2>&1
  } >> "${RESULTS_FILE}"
}

########################################
# 4/5. Fill the drive with test data (Plan A / Plan B)
########################################

create_dummy_data() {
  local mnt="$1"
  local target_percent="$2"

  case "${TEST_STRATEGY}" in
    flag)
      # Plan A: one small "needle" file with a unique marker string,
      # plus random filler to bring the drive up to target_percent full.
      log "Creating dummy filler + flag file (Plan A) on ${mnt}"

      local marker
      marker="FS_TEST_MARKER_$(date +%s)_${RANDOM}"
      {
        echo "Recovery-test flag file."
        echo "MARKER:${marker}"
      } > "${mnt}/${FLAG_FILE_NAME}"
      # Stored on the HOST, not the USB, so it survives the wipe step.
      echo "${marker}" > "${WORK_DIR}/current_marker.txt"

      local i=0 used_percent
      while true; do
        used_percent=$(df --output=pcent "${mnt}" | tail -1 | tr -dc '0-9')
        [ "${used_percent}" -ge "${target_percent}" ] && break
        dd if=/dev/urandom of="${mnt}/dummy_${i}.bin" bs=1M count=50 status=none || break
        i=$((i + 1))
      done
      ;;

    photo)
      # TODO(team): Plan B implementation. Rough outline:
      #
      #   1. Generate solid-colour square PNGs (needs imagemagick):
      #        for i in $(seq 1 N); do
      #          colour=$(printf '#%06x' $((RANDOM * RANDOM % 16777216)))
      #          convert -size 512x512 xc:"${colour}" "${mnt}/photo_${i}.png"
      #        done
      #
      #   2. Hash every photo BEFORE the wipe and save the hashes
      #      somewhere on the HOST (not the USB), keyed by fs+run:
      #        sha256sum "${mnt}"/photo_*.png \
      #          > "${WORK_DIR}/prehash_${fs_name}_run${run}.txt"
      #
      #   3. After recovery (post step 7), re-hash whatever PhotoRec /
      #      ddrescue pulled out of the image and diff against the
      #      prehash file.
      #
      #   4. For any hash mismatch, decide *why*: compare embedded
      #      metadata only (exiftool before/after) vs. actual pixel
      #      data (ImageMagick `compare`, or just re-derive a hash of
      #      the raw pixel buffer rather than the whole file) to tell
      #      "metadata changed" apart from "data blocks were actually
      #      overwritten."
      #
      # Still fill the rest of the drive with random filler as in the
      # "flag" branch above once photos are in place.
      log "ERROR: Plan B (photo strategy) is not implemented yet."
      exit 1
      ;;

    *)
      log "ERROR: Unknown TEST_STRATEGY '${TEST_STRATEGY}'"
      exit 1
      ;;
  esac
}

########################################
# 6. Wipe the drive (format vs rm -rf)
########################################

wipe_usb() {
  local mnt="$1"
  local mkfs_cmd="$2"     # same fs re-applied, for the "format" method
  local dev="/dev/${TARGET_SDX}"

  case "${WIPE_METHOD}" in
    format)
      log "Wiping via quick reformat: ${mkfs_cmd}"
      sudo umount "${mnt}" 2>/dev/null || true
      sudo bash -c "${mkfs_cmd}"
      ;;
    rm)
      log "Wiping via rm -rf contents of ${mnt}"
      sudo rm -rf --one-file-system "${mnt:?}"/*
      sudo umount "${mnt}" 2>/dev/null || true
      ;;
    *)
      log "ERROR: Unknown WIPE_METHOD '${WIPE_METHOD}'"
      exit 1
      ;;
  esac

  # TODO(team): decide if you also want an "unallocated space only"
  # variant later (e.g. delete just the flag file / just the photos
  # instead of the whole drive) to compare against a full wipe.
  unset dev
}

########################################
# 7. Recover with ddrescue, check for the flag, log timing
########################################

step_7_ddrescue_times_examine() {
  local fs_name="$1"
  local run_num="$2"
  local dev="/dev/${TARGET_SDX}"
  local img="${IMAGE_DIR}/${fs_name}_run${run_num}.img"
  local rescue_log="${IMAGE_DIR}/${fs_name}_run${run_num}.ddrescue.log"

  mkdir -p "${IMAGE_DIR}"
  log "Starting ddrescue recovery: fs=${fs_name} run=${run_num}"

  local start_ts end_ts elapsed
  start_ts=$(date +%s)

  # -f force, -d direct disk access (skip kernel cache), -r3 retry bad
  # sectors 3x. TODO(team): tune retry count / add -R (reverse pass) if
  # you want to push recovery harder at the cost of time.
  sudo ddrescue -f -d -r3 "${dev}" "${img}" "${rescue_log}"

  end_ts=$(date +%s)
  elapsed=$((end_ts - start_ts))

  local marker="" found="no" recovered_bytes=0
  [ -f "${WORK_DIR}/current_marker.txt" ] && marker=$(cat "${WORK_DIR}/current_marker.txt")
  [ -f "${img}" ] && recovered_bytes=$(stat -c%s "${img}")

  if [ -n "${marker}" ] && grep -a -q "${marker}" "${img}" 2>/dev/null; then
    found="yes"
  fi

  # TODO(team): for a closer match to the reference paper, run PhotoRec
  # against ${img} here instead of / in addition to the raw grep, e.g.:
  #   photorec /d "${WORK_DIR}/recovered/${fs_name}_run${run_num}" /cmd "${img}" ...
  # and then search the carved output directory for the flag / photos.

  log "RESULT fs=${fs_name} run=${run_num} wipe=${WIPE_METHOD} strategy=${TEST_STRATEGY} elapsed_s=${elapsed} image_bytes=${recovered_bytes} flag_found=${found}"
  echo "${fs_name},${run_num},${WIPE_METHOD},${TEST_STRATEGY},${elapsed},${recovered_bytes},${found}" >> "${RESULTS_FILE}"
}

########################################
# Generic per-filesystem test runner (steps 3-7, x NUM_RUNS)
########################################

run_fs_test() {
  local fs_name="$1"
  local mkfs_template="$2"
  local dev="/dev/${TARGET_SDX}"
  local mkfs_cmd="${mkfs_template//\{DEV\}/${dev}}"

  log "=== Starting test suite for filesystem: ${fs_name} (${NUM_RUNS} runs) ==="

  for run in $(seq 1 "${NUM_RUNS}"); do
    log "--- ${fs_name} run ${run}/${NUM_RUNS} ---"

    # Step 3: format USB to the filesystem under test
    sudo umount "${dev}"* 2>/dev/null || true
    sudo bash -c "${mkfs_cmd}"

    # Step 4/5: mount + copy dummy/target data
    sudo mkdir -p "${MOUNT_POINT}"
    # TODO(team): confirm whether your mkfs commands create a
    # partition (${dev}1) or format the whole device directly (${dev});
    # this tries partition first and falls back to the raw device.
    sudo mount "${dev}1" "${MOUNT_POINT}" 2>/dev/null || sudo mount "${dev}" "${MOUNT_POINT}"
    sudo chown "$(id -u):$(id -g)" "${MOUNT_POINT}"   # TODO(team): tighten if needed

    create_dummy_data "${MOUNT_POINT}" "${FILL_TARGET_PERCENT}"
    sync

    # Step 6: wipe (format or rm, per WIPE_METHOD)
    wipe_usb "${MOUNT_POINT}" "${mkfs_cmd}"

    # Step 7: recover, check, log
    step_7_ddrescue_times_examine "${fs_name}" "${run}"
  done
}

# Thin named wrappers -- kept so you can run/debug one filesystem at a
# time by hand if needed, e.g.: `source fs_recovery_experiment.sh; ntfs_tests`
ntfs_tests()  { run_fs_test "ntfs"  "mkfs.ntfs -f {DEV}"; }
ext4_tests()  { run_fs_test "ext4"  "mkfs.ext4 -F {DEV}"; }
exfat_tests() { run_fs_test "exfat" "mkfs.exfat {DEV}"; }
fat32_tests() { run_fs_test "fat32" "mkfs.vfat -F 32 {DEV}"; }
btrfs_tests() { run_fs_test "btrfs" "mkfs.btrfs -f {DEV}"; }
xfs_tests()   { run_fs_test "xfs"   "mkfs.xfs -f {DEV}"; }

########################################
# Main
########################################

main() {
  if [ "$(id -u)" -eq 0 ]; then
    echo "Don't run this script itself as root -- it calls sudo internally where needed." >&2
    exit 1
  fi

  mkdir -p "${WORK_DIR}" "${IMAGE_DIR}"
  init_results_file

  verify_target
  keep_sudo_alive
  benchmark_usb

  # Default: loop over every filesystem in FILESYSTEMS[] using the
  # shared run_fs_test() helper. Comment this out and uncomment
  # individual *_tests() calls below if you only want to run/debug one
  # filesystem at a time.
  for entry in "${FILESYSTEMS[@]}"; do
    fs_name="${entry%%:*}"
    mkfs_template="${entry#*:}"
    run_fs_test "${fs_name}" "${mkfs_template}"
  done

  # ntfs_tests
  # ext4_tests
  # exfat_tests
  # fat32_tests
  # btrfs_tests
  # xfs_tests

  kill "${SUDO_KEEPALIVE_PID}" 2>/dev/null || true
  log "=== All filesystem test suites complete. Results in ${RESULTS_FILE} ==="
}

main "$@"
```

# Deepseek's Answer:

Below is a **skeleton Bash script** you can hand to your team. I’ve converted your pseudocode into real Bash syntax, added safety checks, logging, and placeholders/TODOs where your team still needs to decide things like Plan A vs Plan B, quick-format vs `rm`, PhotoRec carving, and hash comparison.

> **Warning:** This script is destructive. It formats a block device. Test only in a VM or with a disposable USB drive. Double-check `sdx`, `TARGET_PART`, and `uuid` before running.

```bash
#!/usr/bin/env bash
#
# Research Methodology USB filesystem recovery experiment
# Skeleton script: NTFS first, other filesystems to be filled in later.
#
# DESTRUCTIVE: formats /dev/$sdx or /dev/${sdx}1.
# Run with sudo, e.g.:
#   sudo ./usb_fs_recovery.sh
#
set -euo pipefail

# ============================================================
# Step 0: User configuration
# ============================================================

# Manually set these before running.
# Example: sdx="sdb" for /dev/sdb
sdx=""

# Optional original UUID safety check.
# NOTE: mkfs changes the UUID. This check is only useful before the
# first format. For repeated runs, rely on sdx/TARGET_PART and serial.
uuid=""

# Number of times to repeat each filesystem test.
num_of_runs=10

# Plan A = flag file recovery test.
# Plan B = photo/hash comparison test.
PLAN="A"                 # "A" or "B"

# Wipe method: "quickformat" or "rm"
WIPE_METHOD="quickformat"

# Filesystems to eventually test.
# NTFS is implemented first. Others are stubs at the bottom.
FS_LIST=(ntfs ext4 exfat vfat btrfs xfs)

# ============================================================
# Paths and derived variables
# ============================================================

REAL_USER="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$REAL_USER" | cut -d: -f6)"

TARGET_DEV=""
TARGET_PART=""
MOUNT_DIR=""
RESULTS_FILE=""
RECOVERY_DIR=""
DATA_DIR=""
PHOTO_DIR=""

setup_paths() {
  TARGET_DEV="/dev/${sdx}"
  TARGET_PART="${TARGET_DEV}1"   # adjust if your USB uses a different partition layout

  RESULTS_FILE="$USER_HOME/Downloads/results.txt"
  RECOVERY_DIR="$USER_HOME/Downloads/usb_recovery_$(date +%Y%m%d_%H%M%S)"

  # TODO: point these at your actual dummy data / photo directories.
  DATA_DIR="$USER_HOME/Downloads/dummy_data"
  PHOTO_DIR="$USER_HOME/Downloads/photos"

  mkdir -p "$RECOVERY_DIR"
}

# ============================================================
# Utility functions
# ============================================================

die() {
  echo "ERROR: $*" >&2
  exit 1
}

log() {
  printf '%s\t%s\n' "$(date -Is)" "$*" | tee -a "$RESULTS_FILE"
}

require_root() {
  [[ "${EUID}" -eq 0 ]] || die "Run this script with sudo/root."
}

init_results() {
  mkdir -p "$(dirname "$RESULTS_FILE")"
  : > "$RESULTS_FILE"
  chown "$REAL_USER:$REAL_USER" "$RESULTS_FILE" 2>/dev/null || true

  {
    echo "# USB filesystem recovery experiment"
    echo "# started: $(date -Is)"
    echo -e "timestamp\tfs\trun\twipe_method\trecovery_s\timage_size_bytes\trecovery_rate_MBps\tflag_found\tnotes"
  } >> "$RESULTS_FILE"
}

check_target() {
  [[ -n "$sdx" ]] || die "Set sdx at the top of the script."
  [[ -b "$TARGET_DEV" ]] || die "Not a block device: $TARGET_DEV"

  # Refuse to use the disk that hosts /
  local root_src root_disk
  root_src="$(findmnt -n -o SOURCE / || true)"
  root_disk="$(lsblk -no PKNAME "$root_src" 2>/dev/null | head -1 || true)"

  [[ "$sdx" != "$root_disk" ]] || die "Refusing to use root disk: $sdx"

  if [[ -n "$uuid" ]]; then
    local actual
    actual="$(lsblk -no UUID "$TARGET_PART" 2>/dev/null | head -1 || true)"
    [[ "$actual" == "$uuid" ]] || die "UUID mismatch on $TARGET_PART: got '$actual'"
  fi
}

check_device_exists() {
  [[ -b "$TARGET_DEV" ]] || die "Target device disappeared: $TARGET_DEV"
}

# ============================================================
# Step 1: Results file
# ============================================================

# init_results is called from main().

# ============================================================
# Step 2: Benchmark / baseline
# ============================================================

benchmark_usb() {
  log "=== Baseline / benchmark ==="

  lsblk -o NAME,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINT,MODEL,SERIAL "$TARGET_DEV" \
    | tee -a "$RESULTS_FILE"

  # SMART may need -d sat for some USB bridges.
  # TODO: adjust device type if smartctl fails.
  sudo smartctl -a "$TARGET_DEV" 2>&1 | tee -a "$RESULTS_FILE" || true

  sudo hdparm -tT "$TARGET_DEV" 2>&1 | tee -a "$RESULTS_FILE" || true

  # Read-only badblocks. This can take a long time.
  # Uncomment if you want a bad-sector baseline.
  # sudo badblocks -sv "$TARGET_DEV" 2>&1 | tee -a "$RESULTS_FILE" || true
}

# ============================================================
# Mount / unmount helpers
# ============================================================

unmount_usb() {
  local p

  # Unmount any partitions of the target device.
  for p in "${TARGET_DEV}"*; do
    [[ -e "$p" ]] || continue
    if findmnt -n -S "$p" >/dev/null 2>&1; then
      sudo umount "$p" || true
    fi
  done

  if [[ -n "${MOUNT_DIR:-}" ]] && mountpoint -q "$MOUNT_DIR" 2>/dev/null; then
    sudo umount "$MOUNT_DIR" || true
  fi
}

mount_usb() {
  local fs="$1"

  MOUNT_DIR="$(mktemp -d /tmp/usb-test.XXXXXX)"

  case "$fs" in
    ntfs)
      sudo mount -t ntfs-3g "$TARGET_PART" "$MOUNT_DIR"
      ;;
    exfat)
      sudo mount -t exfat "$TARGET_PART" "$MOUNT_DIR"
      ;;
    ext4)
      sudo mount -t ext4 "$TARGET_PART" "$MOUNT_DIR"
      ;;
    vfat|fat32)
      sudo mount -t vfat "$TARGET_PART" "$MOUNT_DIR"
      ;;
    btrfs)
      sudo mount -t btrfs "$TARGET_PART" "$MOUNT_DIR"
      ;;
    xfs)
      sudo mount -t xfs "$TARGET_PART" "$MOUNT_DIR"
      ;;
    *)
      die "Unsupported filesystem for mount: $fs"
      ;;
  esac
}

# ============================================================
# Format helper
# ============================================================

format_fs() {
  local fs="$1"

  unmount_usb

  case "$fs" in
    ntfs)
      # -f = fast format, -F = force
      sudo mkfs.ntfs -f -F "$TARGET_PART"
      ;;
    exfat)
      sudo mkfs.exfat "$TARGET_PART"
      ;;
    ext4)
      sudo mkfs.ext4 -F "$TARGET_PART"
      ;;
    vfat|fat32)
      sudo mkfs.vfat -F 32 "$TARGET_PART"
      ;;
    btrfs)
      sudo mkfs.btrfs -f "$TARGET_PART"
      ;;
    xfs)
      sudo mkfs.xfs -f "$TARGET_PART"
      ;;
    *)
      die "Unsupported filesystem for format: $fs"
      ;;
  esac

  sync
  sudo partprobe "$TARGET_DEV" 2>/dev/null || true
  sleep 1
}

# ============================================================
# Steps 4 and 5: Populate USB with dummy data
# ============================================================

populate_data() {
  local fs="$1"
  local run="$2"

  sudo mkdir -p "$MOUNT_DIR"

  if [[ "$PLAN" == "A" ]]; then
    # Plan A: junk data + flag.txt
    [[ -d "$DATA_DIR" ]] || die "DATA_DIR not found: $DATA_DIR"

    sudo cp -a "$DATA_DIR"/. "$MOUNT_DIR"/
    echo "FLAG{${fs}_${run}_$(date +%s)}" | sudo tee "$MOUNT_DIR/flag.txt" >/dev/null

  elif [[ "$PLAN" == "B" ]]; then
    # Plan B: photos / solid-colour images + pre-hashes
    [[ -d "$PHOTO_DIR" ]] || die "PHOTO_DIR not found: $PHOTO_DIR"

    sudo cp -a "$PHOTO_DIR"/. "$MOUNT_DIR"/

    # Save pre-test hashes for later comparison.
    (
      cd "$PHOTO_DIR"
      find . -type f -print0 | xargs -0 sha256sum
    ) > "$RECOVERY_DIR/${fs}_run${run}_before.sha256"

  else
    die "Unknown PLAN: $PLAN"
  fi

  sync
}

# ============================================================
# Step 6: Wipe / delete contents
# ============================================================

wipe_data() {
  local method="$1"
  local fs="$2"

  unmount_usb

  if [[ "$method" == "quickformat" ]]; then
    format_fs "$fs"

  elif [[ "$method" == "rm" ]]; then
    mount_usb "$fs"
    sudo rm -rf "$MOUNT_DIR"/* "$MOUNT_DIR"/.[!.]* "$MOUNT_DIR"/..?* 2>/dev/null || true
    sync
    unmount_usb

  else
    die "Unknown WIPE_METHOD: $method"
  fi
}

# ============================================================
# Step 7: ddrescue timing + examine recovery
# ============================================================

step_7_ddrescue_times_examine() {
  local fs="$1"
  local run="$2"

  local image="$RECOVERY_DIR/${fs}_run${run}.img"
  local map="$image.map"
  local dlog="$RECOVERY_DIR/${fs}_run${run}_ddrescue.log"

  local start end elapsed size rate flag_found notes

  mkdir -p "$RECOVERY_DIR"

  start="$(date +%s.%N)"

  # -f force, -n no scrape, -r1 retry once.
  # Adjust source to TARGET_PART if you only want the filesystem,
  # or keep TARGET_DEV to image the whole USB device.
  sudo ddrescue -f -n -r1 "$TARGET_DEV" "$image" "$map" >"$dlog" 2>&1 || true

  end="$(date +%s.%N)"
  elapsed="$(awk -v s="$start" -v e="$end" 'BEGIN{printf "%.3f", e-s}')"

  size="$(stat -c %s "$image" 2>/dev/null || echo 0)"
  rate="$(awk -v b="$size" -v t="$elapsed" 'BEGIN{if(t>0) printf "%.2f", b/t/1024/1024; else print "0"}')"

  flag_found="n/a"

  if [[ "$PLAN" == "A" ]]; then
    if grep -a -q "FLAG{" "$image"; then
      flag_found="yes"
    else
      flag_found="no"
    fi
  fi

  notes="ddrescue_log=$dlog map=$map"

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date -Is)" "$fs" "$run" "$WIPE_METHOD" "$elapsed" "$size" "$rate" "$flag_found" "$notes" \
    | tee -a "$RESULTS_FILE"

  # ----------------------------------------------------------
  # TODO for Plan B / better carving:
  # 1. Run PhotoRec against the image:
  #      sudo photorec /log /d "$RECOVERY_DIR/${fs}_run${run}_photorec" /cmd "$image" search
  #
  # 2. Compare recovered files against the before-hashes:
  #      cd recovered_dir
  #      sha256sum -c "$RECOVERY_DIR/${fs}_run${run}_before.sha256"
  #
  # 3. Record how many hashes matched, changed, or were missing.
  # ----------------------------------------------------------
}

# ============================================================
# Generic filesystem test runner
# ============================================================

run_fs_tests() {
  local fs="$1"

  log "=== Starting $fs tests ==="

  for run in $(seq 1 "$num_of_runs"); do
    check_device_exists

    echo ">>> $fs run $run / $num_of_runs"

    # Step 3: format
    format_fs "$fs"

    # Steps 4-5: mount and copy data
    mount_usb "$fs"
    populate_data "$fs" "$run"
    unmount_usb

    # Step 6: wipe
    wipe_data "$WIPE_METHOD" "$fs"

    # Step 7: recover and examine
    step_7_ddrescue_times_examine "$fs" "$run"
  done

  log "=== Finished $fs tests ==="
}

# ============================================================
# Filesystem-specific wrappers
# ============================================================

ntfs_tests() {
  run_fs_tests "ntfs"
}

# TODO: fill these in later.
# ext4_tests()  { run_fs_tests "ext4"; }
# exfat_tests() { run_fs_tests "exfat"; }
# fat32_tests() { run_fs_tests "vfat"; }
# btrfs_tests() { run_fs_tests "btrfs"; }
# xfs_tests()   { run_fs_tests "xfs"; }

# ============================================================
# Cleanup
# ============================================================

cleanup() {
  unmount_usb || true

  if [[ -n "${MOUNT_DIR:-}" && -d "$MOUNT_DIR" ]]; then
    rmdir "$MOUNT_DIR" 2>/dev/null || true
  fi
}

trap cleanup EXIT

# ============================================================
# Main
# ============================================================

main() {
  require_root
  setup_paths
  check_target
  init_results
  benchmark_usb

  ntfs_tests

  # Uncomment as they are implemented:
  # ext4_tests
  # exfat_tests
  # fat32_tests
  # btrfs_tests
  # xfs_tests
}

main "$@"
```

## Key gaps your team still needs to fill in

1. **Set `sdx` and `uuid`** at the top.  
   Example: `sdx="sdb"` means `/dev/sdb`. Confirm whether you want to format `/dev/sdb1` or the whole `/dev/sdb`.

2. **Decide `TARGET_PART`**  
   Most USB drives have one partition, e.g. `/dev/sdb1`. The script currently uses `TARGET_PART="${TARGET_DEV}1"`. If you really format the whole disk, change this carefully.

3. **Choose `PLAN="A"` or `"B"`**  
   - Plan A: fill with dummy data + `flag.txt`, then grep the ddrescue image for `FLAG{`.
   - Plan B: copy photos, save pre-hashes, then later run PhotoRec and compare hashes.

4. **Choose `WIPE_METHOD`**  
   - `"quickformat"` uses `mkfs` again.
   - `"rm"` mounts and deletes files with `rm -rf`.

5. **Install required tools**  
   Depending on distro:
   ```bash
   sudo apt install ntfs-3g exfatprogs exfat-fuse dosfstools e2fsprogs btrfs-progs xfsprogs gddrescue smartmontools hdparm testdisk
   ```

6. **Complete PhotoRec / carving step**  
   `ddrescue` only creates an image. To actually recover files, your team should add PhotoRec/foremost/scalpel against the image, then compare hashes for Plan B.

7. **Results file**  
   The script writes a TSV-like `results.txt` to `~/Downloads/results.txt`. You may want to switch to `.csv` if you plan to graph it.

8. **Safety note**  
   The UUID check only works before the first `mkfs`, because formatting changes the UUID. For repeated runs, rely on `sdx`, serial number, and physical verification.