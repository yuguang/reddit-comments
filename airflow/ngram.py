"""
### Tutorial Documentation
Documentation that goes along with the Airflow tutorial located
[here](http://pythonhosted.org/airflow/tutorial.html)
"""
from airflow import DAG
from airflow.operators import BashOperator
from datetime import datetime, timedelta
from settings import default_args

dag = DAG('reddit_comments', default_args=default_args, schedule_interval=timedelta(2))


pre = BashOperator(
    task_id='ngrams_batch',
    bash_command='tasks/setup_dirs.sh',
    depends_on_past=False,
    dag=dag)

t1 = BashOperator(
    task_id='ngrams_batch',
    bash_command='tasks/run_ngrams_batch.sh',
    depends_on_past=False,
    dag=dag)

t2 = BashOperator(
    task_id='ngrams_optimize',
    depends_on_past=True,
    bash_command='tasks/optimize_ngrams.sh',
    dag=dag)

t1.set_upstream(pre)
t2.set_upstream(t1)