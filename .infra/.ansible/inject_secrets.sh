#!/bin/bash

# Define the target file
TARGET_FILE=".env"

# Loop through all GitLab CI variables starting with "SECREET_"
for var in $(compgen -e); do
    if [[ $var == SECRET_* ]]; then
        if grep -q "$var" $TARGET_FILE; then
            # Replace the variable in the target file with its value
            echo "'$var' ..."
            sed -i "s|$var|${!var}|g" "$TARGET_FILE"
            echo "Replaced in $TARGET_FILE."
        fi
    fi
done

awk '{for(i=1;i<=NF;i++) if ($i ~ /=SECRET_/) print $i}' $TARGET_FILE

echo "Replacements completed in $TARGET_FILE."