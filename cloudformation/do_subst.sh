#!/bin/bash -ev
# carry out substitution of {$1} with the given value ($2)
if [ -z "$1" -o -z "$2" -o -z "$3" ]
then
  echo "Usage: $0 file key value"
  exit 1
fi

FILE=$1
KEY=$2
VALUE=$3

sed -i "s|{${KEY}}|${VALUE}|g" ${FILE}
