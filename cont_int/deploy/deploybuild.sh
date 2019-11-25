#!/bin/bash
USRDIR=/home/airflowusr
cd $USRDIR

SERVUID=$(curl http://169.254.169.254/latest/meta-data/instance-id/)
SPARK_DISTRIBUTION=spark-2.2.0-bin-hadoop2.7

rm $USRDIR/lastdepgrp*

if [ "$DEPLOYMENT_GROUP_NAME" == "Dev-Airflow" ]; then
  touch $USRDIR/lastdepgrp=dev-airflow.txt
  mkdir -p /home/airflowusr/gothamtmp/
  # spark install
  rm -f $USRDIR/gothamtmp/$SPARK_DISTRIBUTION.tgz
  wget -P $USRDIR/gothamtmp https://d3kbcqa49mib13.cloudfront.net/$SPARK_DISTRIBUTION.tgz
  tar -xf $USRDIR/gothamtmp/$SPARK_DISTRIBUTION.tgz -C $USRDIR
  mv $USRDIR/$SPARK_DISTRIBUTION $USRDIR/spark
  # download extra JARs for spark-s3 connectivity
  rm -f $USRDIR/gothamtmp/hadoop-aws-2.7.3.jar
  wget -P $USRDIR/gothamtmp http://central.maven.org/maven2/org/apache/hadoop/hadoop-aws/2.7.3/hadoop-aws-2.7.3.jar
  mv $USRDIR/gothamtmp/hadoop-aws-2.7.3.jar $USRDIR/spark/jars/
  rm -f $USRDIR/gothamtmp/aws-java-sdk-1.7.4.jar
  wget -P $USRDIR/gothamtmp http://central.maven.org/maven2/com/amazonaws/aws-java-sdk/1.7.4/aws-java-sdk-1.7.4.jar
  mv $USRDIR/gothamtmp/aws-java-sdk-1.7.4.jar $USRDIR/spark/jars/
  source $USRDIR/gothamdeploy/cont_int/deploy/spark_env.sh
  pkill -F $USRDIR/gotham/airflow/airflow-webserver.pid
  pkill -F $USRDIR/gotham/airflow/airflow-scheduler.pid
  pkill -f webserver
  pkill -f scheduler
  ps aux  |  grep -i airflow-webserver  |  awk '{print $2}'  |  xargs sudo kill -9
  ps aux  |  grep -i scheduler  |  awk '{print $2}'  |  xargs sudo kill -9
  cp -f $USRDIR/gothamdeploy/cont_int/config/airflow_dev.cfg $USRDIR/gotham/airflow/airflow.cfg
  /home/airflowusr/venv/bin/python /home/airflowusr/venv/bin/airflow resetdb -y
  mkdir -p $USRDIR/gotham/airflow/dags
  rm -f $USRDIR/gotham/airflow/dags/*.py
  cp -f $USRDIR/gothamdeploy/airflow/dags/*.py $USRDIR/gotham/airflow/dags/
  rm -rf $USRDIR/gotham/airflow/plugins
  cp -rf $USRDIR/gothamdeploy/airflow/plugins $USRDIR/gotham/airflow/plugins
  rm -rf $USRDIR/gotham/airflow/submodules
  cp -rf $USRDIR/gothamdeploy/airflow/submodules $USRDIR/gotham/airflow/submodules
  rm -rf $USRDIR/gotham/airflow/scala
  cp -rf $USRDIR/gothamdeploy/airflow/scala $USRDIR/gotham/airflow/scala
  rm -rf $USRDIR/gotham/airflow/databricks
  cp -rf $USRDIR/gothamdeploy/airflow/databricks $USRDIR/gotham/airflow/databricks
  rm -rf $USRDIR/gotham/airflow/spark_scripts/
  cp -rf $USRDIR/gothamdeploy/airflow/spark_scripts $USRDIR/gotham/airflow/spark_scripts  
  rm -rf $USRDIR/gotham/airflow/sql
  cp -rf $USRDIR/gothamdeploy/airflow/sql $USRDIR/gotham/airflow/sql
  rm -rf $USRDIR/gotham/airflow/resources
  cp -rf $USRDIR/gothamdeploy/airflow/resources $USRDIR/gotham/airflow/resources
  rm -rf $USRDIR/gotham/airflow/glue-prod
  cp -rf $USRDIR/gothamdeploy/airflow/glue-prod $USRDIR/gotham/airflow/glue-prod
  cp -f $USRDIR/gothamdeploy/cont_int/keys/Prod-AutomatedEMR.pem $USRDIR/Prod-AutomatedEMR.pem
  cp -rf $USRDIR/gothamdeploy/cont_int/bin $USRDIR/bin
  source $USRDIR/venv/bin/activate
  pip install -r $USRDIR/gothamdeploy/requirements.txt
  export AIRFLOW_HOME=$USRDIR/gotham/airflow/
  nohup $USRDIR/venv/bin/python $USRDIR/venv/bin/airflow webserver &>/dev/null &
  nohup $USRDIR/venv/bin/python $USRDIR/venv/bin/airflow scheduler &>/dev/null &
elif [ "$DEPLOYMENT_GROUP_NAME" == "Prod-Airflow" ]; then
  touch $USRDIR/lastdepgrp=prod-airflow.txt
  mkdir -p /home/airflowusr/gothamtmp/
  # spark install
  rm -f $USRDIR/gothamtmp/$SPARK_DISTRIBUTION.tgz
  wget -P $USRDIR/gothamtmp https://d3kbcqa49mib13.cloudfront.net/$SPARK_DISTRIBUTION.tgz
  tar -xf $USRDIR/gothamtmp/$SPARK_DISTRIBUTION.tgz -C $USRDIR
  mv $USRDIR/$SPARK_DISTRIBUTION $USRDIR/spark
  # download extra JARs for spark-s3 connectivity
  rm -f $USRDIR/gothamtmp/hadoop-aws-2.7.3.jar
  wget -P $USRDIR/gothamtmp http://central.maven.org/maven2/org/apache/hadoop/hadoop-aws/2.7.3/hadoop-aws-2.7.3.jar
  mv $USRDIR/gothamtmp/hadoop-aws-2.7.3.jar $USRDIR/spark/jars/
  rm -f $USRDIR/gothamtmp/aws-java-sdk-1.7.4.jar
  wget -P $USRDIR/gothamtmp http://central.maven.org/maven2/com/amazonaws/aws-java-sdk/1.7.4/aws-java-sdk-1.7.4.jar
  mv $USRDIR/gothamtmp/aws-java-sdk-1.7.4.jar $USRDIR/spark/jars/
  source $USRDIR/gothamdeploy/cont_int/deploy/spark_env.sh
  pkill -F $USRDIR/gotham/airflow/airflow-scheduler.pid
  pkill -F $USRDIR/gotham/airflow/airflow-webserver.pid
  pkill -f webserver
  pkill -f scheduler  
  ps aux  |  grep -i scheduler  |  awk '{print $2}'  |  xargs sudo kill -9
  ps aux  |  grep -i airflow-webserver  |  awk '{print $2}'  |  xargs sudo kill -9
  mkdir -p $USRDIR/gotham/airflow/dags 
  cp -f $USRDIR/gothamdeploy/cont_int/config/airflow_prod.cfg $USRDIR/gotham/airflow/airflow.cfg
  rm -f $USRDIR/gotham/airflow/dags/*.py
  cp -f $USRDIR/gothamdeploy/airflow/dags/*.py $USRDIR/gotham/airflow/dags/
  rm -rf $USRDIR/gotham/airflow/plugins
  cp -rf $USRDIR/gothamdeploy/airflow/plugins $USRDIR/gotham/airflow/plugins
  rm -rf $USRDIR/gotham/airflow/submodules
  cp -rf $USRDIR/gothamdeploy/airflow/submodules $USRDIR/gotham/airflow/submodules
  rm -rf $USRDIR/gotham/airflow/scala
  cp -rf $USRDIR/gothamdeploy/airflow/scala $USRDIR/gotham/airflow/scala
  rm -rf $USRDIR/gotham/airflow/databricks
  cp -rf $USRDIR/gothamdeploy/airflow/databricks $USRDIR/gotham/airflow/databricks
  rm -rf $USRDIR/gotham/airflow/spark_scripts/
  cp -rf $USRDIR/gothamdeploy/airflow/spark_scripts $USRDIR/gotham/airflow/spark_scripts
  rm -rf $USRDIR/gotham/airflow/sql
  cp -rf $USRDIR/gothamdeploy/airflow/sql $USRDIR/gotham/airflow/sql
  rm -rf $USRDIR/gotham/airflow/resources
  cp -rf $USRDIR/gothamdeploy/airflow/resources $USRDIR/gotham/airflow/resources
  rm -rf $USRDIR/gotham/airflow/glue-prod
  cp -rf $USRDIR/gothamdeploy/airflow/glue-prod $USRDIR/gotham/airflow/glue-prod
  cp -f $USRDIR/gothamdeploy/cont_int/keys/Prod-AutomatedEMR.pem $USRDIR/Prod-AutomatedEMR.pem
  rm -rf $USRDIR/gotham/cont_int
  cp -rf $USRDIR/gothamdeploy/cont_int $USRDIR/gotham/cont_int
  source $USRDIR/venv/bin/activate
  pip install -r $USRDIR/gothamdeploy/requirements.txt
  export AIRFLOW_HOME=$USRDIR/gotham/airflow
  if [ $SERVUID == "i-f7d67a0f" ]; then
    echo "Master Node"
    export AIRFLOW_HOME=$USRDIR/gotham/airflow
    nohup $USRDIR/venv/bin/python $USRDIR/venv/bin/airflow webserver &>/dev/null &
    nohup $USRDIR/venv/bin/python $USRDIR/venv/bin/airflow scheduler &>/dev/null &
  else
    echo "Worker Node"
  fi
else
  touch $USRDIR/lastdepgrp=unknown.txt
  echo "No deployment group name"
fi
