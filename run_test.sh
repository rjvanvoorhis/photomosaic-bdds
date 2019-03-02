#!/usr/bin/env bash

export BDD_DIRECTORY=$(pwd)

go_home() {
  cd ${BDD_DIRECTORY}
}

start_swarm() {
   ERROR_MESSAGE=$(docker swarm init 2>&1)
   if [[ "$ERROR_MESSAGE" ]]
   then
      tmpfile=$(mktemp);
      echo "$ERROR_MESSAGE" >> tmpfile;
      ADDR=$(grep -oP '(?<=\().*(?= and)' tmpfile)
      echo "ADDR SET TO: $ADDR"
      rm tmpfile
      docker swarm init --advertise-addr=$ADDR
   fi
}

launch_stack() {
    go_home
    export ENVIRONMENT=local
    setup_env
    docker-compose up -d
    poll_stack
}

launch_swarm() {
    go_home
    if [[ "$(docker info | grep Swarm | sed 's/Swarm: //g')" == "inactive" ]]; then
        echo "Starting Swarm Mode";
        start_swarm;
    else
        echo "Already in swarm mode, updating stack";
    fi
    export ENVIRONMENT=swarm
    setup_env
    cd faas_stack
    bash deploy_stack.sh --no-auth &&
    poll_stack &&
    go_home
    faas-cli deploy
}

setup_env() {
  source postdeactivate.sh
  python reset_environment.py
  source postactivate.sh
  rm postactivate.sh
}

spin_down() {
   if [[ "$ENVIRONMENT" == "swarm" ]]
   then
       docker swarm leave --force
   else
       docker-compose down
   fi
   rm .env
}

poll_stack(){
    WEBSERV="$MOSAIC_API_URL_EXTERNAL/system/health_check"
    MEDIA_BUCKET="${MEDIA_BUCKET:-images}"
    echo "Checking health at ${WEBSERV}"
    COUNTER=0
    sleep 5
    while [[ ${COUNTER} -lt 10 ]]; do

        echo The counter is ${COUNTER}
        sleep 5
        if [[ "$(curl -i -s "$WEBSERV" | grep -nE 200)" ]]
            then
            # if the 200 status code is in the content
            echo "The stack is working fine"
            break
        else
            echo "Error, checking if media bucket exists";

            curl --request PUT "${S3_EXTERNAL_URL}/${MEDIA_BUCKET}";
            echo $(curl -i -s "$WEBSERV")
            let COUNTER=COUNTER+1
        fi
    done
}
