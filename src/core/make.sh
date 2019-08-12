#/bin/bash

PWD=`pwd`
FILE_DIR=`dirname $0`
APP_DIR=`realpath ${FILE_DIR}`
MAKE_TEMP_FILE=${APP_DIR}/make_is_working
MAKE_DOWN_FILE=${APP_DIR}/make_is_done

while [ -f "$MAKE_TEMP_FILE" ]
do
    echo $MAKE_TEMP_FILE
    sleep 1
done
echo start make at `date`
touch ${MAKE_TEMP_FILE}

export __SERVER_MAKE=1
export USER=root
echo ${APP_DIR}
cd ${APP_DIR}/utils/
python protobuf.py $1

rm ${MAKE_TEMP_FILE}
echo "fci make finished at" `date`
echo `date` > ${MAKE_DOWN_FILE}