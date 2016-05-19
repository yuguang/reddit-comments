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

# t1, t2 and t3 are examples of tasks created by instantiating operators
t1 = BashOperator(
    task_id='ngrams_batch',
    bash_command='tasks/run_ngrams_batch.sh',
    depends_on_past=True,
    dag=dag)

t2 = BashOperator(
    task_id='ngrams_optimize',
    depends_on_past=True,
    bash_command='tasks/optimize_ngrams.sh',
    dag=dag)

t2.set_upstream(t1)