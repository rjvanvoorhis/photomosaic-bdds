#!/usr/bin/env bash


# Setup
export BDD_DIRECTORY=$(pwd)

go_home() {
  cd ${BDD_DIRECTORY}
}

setup_env() {
  source postdeactivate.sh
  python reset_environment.py
  source postactivate.sh
  rm postactivate.sh
}

spin_down_stack() {
   go_home
   if is_in_swarm
   then
       leave_swarm
   else
       docker-compose down
   fi
   rm .env
}


# OpenFaaS
launch_faas() {
    go_home
    cd faas_stack
    bash deploy_stack.sh --no-auth &&
    poll_stack &&
    go_home
    faas-cli deploy
}


# Swarm Config
is_in_swarm () {
    if [[ "$(docker info | grep Swarm | sed 's/Swarm: //g')" == "inactive" ]]; then
        # not in swarm
        return 1
    else
        # true, in swarm
        return 0
    fi
}

leave_swarm() {
   docker swarm leave --force
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

launch_swarm() {
    go_home
    if is_in_swarm; then
        echo "Already in swarm mode, updating stack";
        start_swarm;
    else
        echo "Starting swarm mode ..."
        start_swarm
    fi
    export ENVIRONMENT=swarm
    setup_env
    cd faas_stack
    bash deploy_stack.sh --no-auth &&
    poll_stack &&
    go_home
    faas-cli deploy
}



# Stack
launch_local() {
    if is_in_swarm; then leave_swarm; fi ;
    go_home
    export ENVIRONMENT=local
    setup_env
    docker-compose up -d
    poll_stack
}


launch_stack() {
    spin_down_stack
    if [[ "${ENVIRONMENT}" == "swarm" ]]
    then
        echo "Deploying the stack to the swarm"
        launch_swarm
    else
        echo "Starting the local stack with docker-compose"
        launch_local
    fi
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




# UI setup
go_to_ui() {
    go_home
    UI_REPO_NAME=${UI_REPO_NAME:-photomosaic-fe-v2}
    cd ${UI_REPO_NAME}
}

get_ui_repo() {
    go_home
    UI_REPO_NAME=${UI_REPO_NAME:-photomosaic-fe-v2}
    if [[ ! -d "${UI_REPO_NAME}" ]]; then
        git clone https://github.com/rjvanvoorhis/${UI_REPO_NAME}.git
        cd ${UI_REPO_NAME}
    else
        cd ${UI_REPO_NAME} &&
        git pull
    fi

}

build_ui() {
    # go_home
    # UI_REPO_NAME=${UI_REPO_NAME:-photomosaic-fe-v2}
    # rm -rf ${UI_REPO_NAME}
    # git clone https://github.com/rjvanvoorhis/${UI_REPO_NAME}.git &&
    # cd ${UI_REPO_NAME} &&
    get_ui_repo &&
    python setup.py &&
    docker-compose build
}

launch_ui() {
    go_to_ui
    if is_in_swarm
    then
        echo "Creating the mosaic-ui swarm service"
        docker stack deploy -c docker-compose.yml mosaicfy
    else
        echo "Starting the mosaic-ui container"
        docker-compose up -d
    fi
    echo "UI available at http://${BROADCAST_IP}:${FE_PORT}"
}

deploy_ui() {
    build_ui
    launch_ui
    go_home
}

teardown_ui() {
    go_to_ui &&
    if is_in_swarm
    then
        leave_swarm;
    else
        docker-compose down
    fi
    go_home
}


test_and_deploy() {
    spin_down_stack
    teardown_ui
    go_home
    export ENVIRONMENT=${ENVIRONMENT:-local}
    launch_stack &&
    # if [[ "${ENVIRONMENT}" == "stack"  ]]
    #     then
	# launch_swarm
    # else
    #     launch_stack
    # fi &&
    behave &&
    deploy_ui   
} 
