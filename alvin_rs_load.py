from airflow import DAG
from airflow.operators import PythonOperator
from airflow.hooks import RedshiftHook, S3Hook
from datetime import datetime, timedelta
import logging
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
import os

# Set argument variables
args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['mike@7parkdata.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'start_date': datetime.now() - timedelta(days=1),
    'sla': timedelta(minutes=300),
}
# Create Client-Logging Dag
dag = DAG('Alvin-RS-Load', default_args=args, schedule_interval="0 5 * * *")

column_name_mapping = {
    "date": "date",
    "domain": "varchar(255)",
    "countrycode": "varchar(5)",
    "platform": "varchar(20)",
    "browsertype": "varchar(20)",
    "gender": "varchar(20)",
    "age": "varchar(20)",
    "uniquevisitors": "int",
    "pageviews": "int",
    "episodeid": "varchar(3000)",
    "path": "varchar(3000)",
    "params": "varchar(3000)",
    "loanamount": "int",
    "loanpurpose": "varchar(255)",
    "creditscore": "varchar(255)",
    "udate": "date",
    "domainname": "varchar(255)",
    "uniqueguids": "int",
    "type": "varchar(255)",
    "city": "varchar(255)",
    "province": "varchar(255)",
    "approved": "varchar(20)",
    "n": "varchar(255)"
}
table_types = ['batch', 'auto_upload']
dont_load_or_create = ['auto_upload', ]
dont_load_or_create = []

auto_upload_tables = [
    "int_retailers$checkouts",
    "hulu$streaming_qp",
    "hulu$traffic_qp",
    "netflix$cancels",
    "netflix$signups",
    "netflix$stream",
    "netflix$traffic",
    "amazon$checkouts",
    "amazon$traffic",
    "amazon$checkouts_qp",
    "amazon$primecancels_qp",
    "amazon$primesignups_qp",
    "amazon$traffic_qp",
    "ebay$traffic_qp",
    "ebay$checkouts_qp",
    "etsy$checkouts",
    "etsy$traffic",
    "flipkart$checkouts",
    "flipkart$traffic",
    "groupon$checkouts",
    "groupon$traffic",
    "homeshop$checkouts",
    "homeshop$traffic",
    "jabong$checkouts",
    "jabong$traffic",
    "limeroad$checkouts",
    "limeroad$traffic",
    "snapdeal$checkouts",
    "snapdeal$traffic",
    "wayfair$checkouts",
    "wayfair$traffic",
    "allmodern$checkouts",
    "allmodern$traffic",
    "birchlane$checkouts",
    "birchlane$traffic",
    "dwellstudio$checkouts",
    "dwellstudio$traffic",
    "jossandmain$checkouts",
    "jossandmain$traffic",
    "lendingclub$borrowers",
    "lendingclub$investors",
    "lendingclub$loan_applications",
    "lendingclub$traffic",
    "lendingclub$traffic_qp",
    "lendingclub$loan_applications_agreggated_qp",
    "prosper$borrowers",
    "prosper$investors",
    "prosper$loan_applications",
    "prosper$traffic",
    "prosper$traffic_qp",
    "prosper$loan_applications_aggregated_qp",
    "creditkarma$borrowers",
    "creditkarma$traffic",
    "creditkarma$traffic_qp",
    "ondeck$borrowers",
    "ondeck$traffic",
    "ondeck$traffic_qp",
    "tripadvisor$traffic_qp",
    "tripadvisor$referrals_qp",
    "tripadvisor$bookings_qp"
]


def send_mail(send_from, send_to, subject, text, password, server='localhost'):
    assert type(send_to) == list
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    smtp = smtplib.SMTP(server)
    smtp.set_debuglevel(False)
    smtp.login(send_from, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


def convert_alvin_schema(schema_text):
    column_names = schema_text.split('|')
    new_schema = ''
    for column_name in column_names:
        column_name = column_name.replace(' ', '').replace('\n', '')
        if column_name in column_name_mapping:
            new_schema += column_name + ' ' + column_name_mapping[column_name] + ',\n'
        else:
            new_schema += column_name + ' varchar(3000),\n'
            print '..........new column!_' + column_name + '_'
    return new_schema[:-2]


def create_tables(**kwargs):
    restricted_create = []
    # restricted_create = ['prosper$borrowers']
    s3_hook = S3Hook('s3incoming')
    rs_hook = RedshiftHook('redshift-rd')
    rs_main_hook = RedshiftHook('redshift')
    bucket_name = '7p-a41b1c8e918c40a5ab352b382a282e20'
    fail_list = []
    success_list = []
    custom_schemas = {}
    rs_main_hook.run("drop schema if exists alvin_batch cascade;")
    rs_main_hook.run("drop schema if exists alvin_auto_upload cascade;")
    rs_main_hook.run("create schema alvin_batch;")
    rs_main_hook.run("create schema alvin_auto_upload;")
    rs_main_hook.run("create table alvin_batch.load_log(udate date, action_source varchar(255), action_type varchar(255), tablename varchar(255));")
    rs_main_hook.run("create table alvin_auto_upload.load_log(udate date, action_source varchar(255), action_type varchar(255), tablename varchar(255));")
    for table_type in table_types:
        key_list = s3_hook.list_objects(bucket_name=bucket_name,prefix=table_type+'/')
        logging.info('Building list of tables.')
        table_list = []
        for key in key_list:
            key_parts = key.key.split('/')
            if len(key_parts) == 5:
                if key_parts[2] != '':
                    table_list.append(key_parts[1] + '$' + key_parts[2])
            elif len(key_parts) == 6:
                    table_list.append(key_parts[1] + '$' + key_parts[2] + '$' + key_parts[3])
        table_list = list(set(table_list))
        create_query = open(os.environ['AIRFLOW_HOME'] + '/sql/alvin/alvin_create_table.sql', 'r').read()
        default_schema = open(os.environ['AIRFLOW_HOME'] + '/sql/alvin/alvin_default_schema.sql', 'r').read()
        for tbl in table_list:
            # print tbl
            tbl_create_query = ''
            if table_type == 'batch':
                for key in key_list:
                    if '.schema' in key.key.split('/')[-1] and table_type + '/' + tbl.replace('$','/') + '/' in key.key:
                        print table_type + '......Custom Schema: ' + tbl
                        # Use custom .schema file
                        tbl_create_query = create_query.format('alvin_' + table_type + '.' + tbl, table_type, convert_alvin_schema(key.get()['Body'].read()),datetime.strftime(datetime.now(),'%Y-%m-%d'))
                        # Add to dict for us in auto_upload
                        custom_schemas[tbl] = tbl_create_query
            else:
                if tbl in custom_schemas:
                    print table_type + '..............Found Custom Schema: ' + tbl
                    tbl_create_query = custom_schemas[tbl].replace('batch', 'auto_upload')
            if tbl_create_query == '':
                print table_type + '...Default Schema: ' + tbl
                # Didn't find a .schema, use default
                tbl_create_query = create_query.format('alvin_' + table_type + '.' + tbl, table_type, default_schema, datetime.strftime(datetime.now(),'%Y-%m-%d'))
            try:
                if tbl not in auto_upload_tables and table_type == 'auto_upload':
                    pass
                else:
                    if len(restricted_create) > 0:
                        if tbl in restricted_create:
                            if table_type not in dont_load_or_create:
                                rs_hook.run(tbl_create_query)
                                rs_main_hook.run(tbl_create_query)
                                success_list.append('alvin' + table_type + '.' + tbl)
                    else:
                        if table_type not in dont_load_or_create:
                            rs_hook.run(tbl_create_query)
                            rs_main_hook.run(tbl_create_query)
                            success_list.append('alvin' + table_type + '.' + tbl)
            except Exception as e:
                rs_hook.get_conn().rollback()
                rs_main_hook.get_conn().rollback()
                print str(e)
                fail_list.append('alvin' + table_type + '.' + tbl)
    temp_html = 'The following table(s) had corrupted .schema files, or another create issue:\n'
    for fail in fail_list:
        temp_html += fail + '\n'
    temp_html += '\n\n\nThe following table(s) were created successfully:\n'
    for success in success_list:
        temp_html += success + '\n'
    SMTPserver = 'smtp.emailsrvr.com'
    sender = 'qa@7parkdata.com'
    pw = '7Parkdata'
    receiver = ['ben@7parkdata.com','daniel@7parkdata.com','kanwal@7parkdata.com','tommy@7parkdata.com','catherine@7parkdata.com']
    subject = '7Park Jumpshot: Table CREATE Log'
    send_mail(sender, receiver, subject, temp_html, pw, SMTPserver)
    logging.info('Email sent.')

def load_tables(**kwargs):
    restricted_load = []
    # restricted_load = ['prosper$borrowers']
    s3_hook = S3Hook('s3incoming')
    rs_hook = RedshiftHook('redshift-rd')
    rs_main_hook = RedshiftHook('redshift')
    fail_list = []
    success_list = []
    for table_type in table_types:
        table_list = []
        bucket_name = '7p-a41b1c8e918c40a5ab352b382a282e20'
        key_list = s3_hook.list_objects(bucket_name=bucket_name, prefix=table_type + '/')
        load_query = open(os.environ['AIRFLOW_HOME'] + '/sql/alvin/alvin_load_table.sql', 'r').read()
        for key in key_list:
            key_parts = key.key.split('/')
            if len(key_parts) == 5:
                if key_parts[2] != '':
                    table_list.append(key_parts[1] + '$' + key_parts[2])
            elif len(key_parts) == 6:
                    table_list.append(key_parts[1] + '$' + key_parts[2] + '$' + key_parts[3])
        table_list = list(set(table_list))
        for tbl in table_list:
            print tbl
            try:
                if tbl not in auto_upload_tables and table_type == 'auto_upload':
                    pass
                else:
                    tbl_parts = tbl.split('$')
                    topic = tbl_parts[0]
                    if len(tbl_parts) == 3:
                        table = tbl_parts[1] + '/' + tbl_parts[2]
                    else:
                        table = tbl_parts[1]
                    if len(restricted_load) > 0:
                        if tbl in restricted_load:
                            if table_type not in dont_load_or_create:
                                rs_hook.run(load_query.format('alvin_' + table_type + '.' + tbl, table_type, topic, table, str(s3_hook.credentials()[0]), str(s3_hook.credentials()[1]), datetime.strftime(datetime.now(),'%Y-%m-%d')))
                                rs_main_hook.run(load_query.format('alvin_' + table_type + '.' + tbl, table_type, topic, table, str(s3_hook.credentials()[0]), str(s3_hook.credentials()[1]), datetime.strftime(datetime.now(),'%Y-%m-%d')))
                                success_list.append('alvin' + table_type + '.' + tbl)
                    else:
                        if table_type not in dont_load_or_create:
                            rs_hook.run(load_query.format('alvin_' + table_type + '.' + tbl, table_type, topic, table, str(s3_hook.credentials()[0]), str(s3_hook.credentials()[1]), datetime.strftime(datetime.now(),'%Y-%m-%d')))
                            rs_main_hook.run(load_query.format('alvin_' + table_type + '.' + tbl, table_type, topic, table, str(s3_hook.credentials()[0]), str(s3_hook.credentials()[1]), datetime.strftime(datetime.now(),'%Y-%m-%d')))
                            success_list.append('alvin' + table_type + '.' + tbl)
            except Exception as e:
                rs_hook.get_conn().rollback()
                rs_main_hook.get_conn().rollback()
                fail_list.append('alvin' + table_type + '.' + tbl)
    print 'The following table(s) failed to load:' + str(fail_list)
    logging.info('The following table(s) failed to load:' + str(fail_list))

    temp_html = 'The following table(s) failed to load:\n'
    for fail in fail_list:
        temp_html += fail + '\n'
    temp_html += '\n\n\nThe following table(s) were loaded successfully:\n'
    for success in success_list:
        temp_html += success + '\n'

    SMTPserver = 'smtp.emailsrvr.com'
    sender = 'qa@7parkdata.com'
    pw = '7Parkdata'
    receiver = ['ben@7parkdata.com','daniel@7parkdata.com','kanwal@7parkdata.com','tommy@7parkdata.com','catherine@7parkdata.com']
    subject = '7Park Jumpshot: Table LOAD Log'
    send_mail(sender, receiver, subject, temp_html, pw, SMTPserver)
    logging.info('Email sent.')

def join_tables(**kwargs):
    rs_hook = RedshiftHook('redshift-rd')
    rs_main_hook = RedshiftHook('redshift')
    table_list_query = """select t1.relname from (
        select relname
        from stv_tbl_perm
        join pg_class on pg_class.oid = stv_tbl_perm.id
        join pg_namespace on pg_namespace.oid = relnamespace
        where nspname = 'alvin_auto_upload'
        group by 1) t1
        join (
        select relname
        from stv_tbl_perm
        join pg_class on pg_class.oid = stv_tbl_perm.id
        join pg_namespace on pg_namespace.oid = relnamespace
        where nspname = 'alvin_batch'
        group by 1) t2
        on t1.relname = t2.relname;"""
    table_list = rs_hook.get_records(table_list_query)
    success_list = []
    fail_list = []
    for table in table_list:
        tbl = table[0]
        join_query = """DROP TABLE IF EXISTS alvin_join.""" + tbl + """;
            CREATE TABLE alvin_join.""" + tbl + """
            (like alvin_batch.""" + tbl + """);
            INSERT INTO alvin_join.""" + tbl + """
            SELECT * FROM alvin_batch.""" + tbl + """;
            INSERT INTO alvin_join.""" + tbl + """
            SELECT * FROM alvin_auto_upload.""" + tbl + """;"""
        try:
            rs_hook.run(join_query)
            rs_main_hook.run(join_query)
            success_list.append(tbl)
        except Exception as e:
            rs_hook.get_conn().rollback()
            rs_main_hook.get_conn().rollback()
            fail_list.append(tbl)
    rs_main_hook.run("drop schema if exists alvin_batch cascade;")
    rs_main_hook.run("drop schema if exists alvin_auto_upload cascade;")
    print 'The following table(s) failed to join:' + str(fail_list)

    temp_html = 'The following table(s) failed to join:\n'
    for fail in fail_list:
        temp_html += fail + '\n'
    temp_html += '\n\n\nThe following table(s) were joined successfully:\n'
    for success in success_list:
        temp_html += success + '\n'

    SMTPserver = 'smtp.emailsrvr.com'
    sender = 'qa@7parkdata.com'
    pw = '7Parkdata'
    receiver = ['ben@7parkdata.com','daniel@7parkdata.com','kanwal@7parkdata.com','tommy@7parkdata.com','catherine@7parkdata.com']
    subject = '7Park Jumpshot: Table Join Log'
    send_mail(sender, receiver, subject, temp_html, pw, SMTPserver)
    logging.info('Email sent.')

def cleanse_data(**kwargs):
    rs_hook = RedshiftHook('redshift-rd')
    rs_main_hook = RedshiftHook('redshift')
    ebay_query = """
        DROP TABLE IF EXISTS alvin_join.ebay$checkouts_qp_clean;
        CREATE TABLE alvin_join.ebay$checkouts_qp_clean(like alvin_join.ebay$checkouts_qp);
        INSERT INTO alvin_join.ebay$checkouts_qp_clean
        SELECT
            udate,'ebay',countrycode,platform,'CHROME',gender,age,'','','',SUM(uniqueguids) AS uniqueguids,0 AS pageviews
        FROM alvin_join.ebay$checkouts_qp
        WHERE (path = '/xo/view' AND params = 'success')
        OR (domain ILIKE '%checkout.payments.%ebay.%' AND path ILIKE '/ws/eBayISAPI.dll' AND params = 'success')
        OR (domain ILIKE '%mbuy%' AND params = 'success')
        OR (domain ILIKE 'pay.ebay%' AND params = 'success')
        OR (domain ILIKE '%ebay.vn' AND path ILIKE '/frontend/payment/success')
        OR (domain = 'order2.ebay.in' AND path ILIKE '/_sparkrop/OrderConfirm')
        GROUP BY udate, countrycode, platform, age, gender"""
    rs_hook.run(ebay_query)
    rs_main_hook.run(ebay_query)


# -- QA the input data --

def send_email(subject, message):
    """Utility function for sending emails."""

    SMTPserver = 'smtp.emailsrvr.com'
    sender = 'qa@7parkdata.com'
    pw = '7Parkdata'
    receivers = ['ben@7parkdata.com','daniel@7parkdata.com','puspal@7parkdata.com']
    send_mail(sender, receivers, subject, message, pw, SMTPserver)
    logging.info('Email sent.')


# -- end function --

def qa_check_for_missing_dates(**kwargs):
    """QA: Check for any missing dates in the input."""

    # Set up execution date, hooks, message
    exec_date = kwargs["ti"].execution_date - timedelta(days=3)
    rs_hook = RedshiftHook('redshift')
    message = ''

    # Retrieve list of tables in schema
    query = 'select table_name from information_schema.tables where table_schema = \'alvin_join\''
    result = rs_hook.get_records(query)
    table_list = map(''.join, result)

    # QA1: Check for missing dates
    logging.info('Checking for missing dates.')
    start_date = datetime.strptime('2014-01-02', '%Y-%m-%d').date()
    end_date = exec_date.date()
    missing = False
    missing_dic = {}
    for table in table_list:
        if table in ('netflix$stream', 'hulu$streaming_qp'):
            query = 'select column_name from information_schema.columns where table_schema = \'alvin_join\' and table_name = \'%s\'' % table
            result = rs_hook.get_records(query)
            column_list = map(''.join, result)
            date_column = 'udate'
            if 'date' in column_list:
                date_column = 'date'
            query = 'select ad.days from sundance.alldays ad left join(select {date_column} from alvin_join.{table_name} group by {date_column}) aj on ad.days = aj.{date_column} where ad.days between \'{start_date}\' and \'{end_date}\' and aj.{date_column} is null order by ad.days'.format(date_column=date_column, table_name=table, start_date=start_date, end_date=end_date)
            result = rs_hook.get_records(query)
            date_list = [date[0] for date in result]
            if date_list:
                missing = True
                missing_dic[table] = []
                for date in date_list:
                    missing_dic[table].append(date)
    if missing:
        logging.info('Missing dates detected.')
        message += 'The following table(s) have missing dates:\n\n'
        for table in missing_dic:
            if missing_dic[table]:
                message += 'alvin_join.%s\n' % table
                for date in missing_dic[table]:
                    message += '\t- %s\n' % date

        subject = '7Park Jumpshot: QA - Missing Dates Found'
        send_email(subject, message)
        logging.info('Failed QA check for missing dates.')
    else:
        logging.info('Passed QA check for missing dates.')


# -- end function --


def qa_check_for_duplicates(**kwargs):
    """QA: Check for duplicates in the input."""

    # Set up execution date, hooks, message
    exec_date = kwargs["ti"].execution_date - timedelta(days=3)
    rs_hook = RedshiftHook('redshift')
    message = ''

    # Retrieve list of tables in schema
    query = 'select table_name from information_schema.tables where table_schema = \'alvin_join\''
    result = rs_hook.get_records(query)
    table_list = map(''.join, result)


    logging.info('Checking for duplicate data.')
    start_date = datetime.strptime('2014-01-02', '%Y-%m-%d').date()
    end_date = exec_date.date()
    duplicate = False
    duplicate_dic = {}
    for table in table_list:
        if table in ('netflix$stream', 'hulu$streaming_qp'):
            query = 'select column_name from information_schema.columns where table_schema = \'alvin_join\' and table_name = \'%s\' and column_name not in (\'%s\')' % (table, '\',\''.join(['uniqueguids', 'uniquevisitors', 'pageviews']))
            result = rs_hook.get_records(query)
            column_list = map(''.join, result)
            date_column = 'udate'
            if 'date' in column_list:
                date_column = 'date'
            query = 'select distinct {date_column} from (select {select_columns}, count(*) from alvin_join.{table_name} group by {select_columns} having count(*) > 1) order by {date_column}'.format(date_column=date_column, table_name=table, select_columns=','.join(column_list))
            result = rs_hook.get_records(query)
            date_list = [date[0] for date in result]
            if date_list:
                duplicate = True
                duplicate_dic[table] = []
                for date in date_list:
                    duplicate_dic[table].append(date)

    if duplicate:
        logging.info('Duplicate data has been detected.')
        message += 'The following table(s) have duplicate data:\n\n'
        for table in duplicate_dic:
            if duplicate_dic[table]:
                message += 'alvin_join.%s\n' % table
                for date in duplicate_dic[table]:
                    message += '\t- %s\n' % date


        subject = '7Park Jumpshot: QA - Duplicates Found'
        send_email(subject, message)
        logging.info('Failed QA check for duplicate data.')
    else:
        logging.info('Passed QA check for duplicate data.')


# -- end function --

def qa_check_for_variation_in_daily_unique_visitors(**kwargs):
    """Check for day-over-day change in total daily unique visitors."""

    THRESHOLD_PERCENT = 10
    LOOKBACK_DAYS = 1

    logging.info('Checking for variation in daily unique visitors.')

    # Set up execution date, hooks, message
    exec_date = kwargs["ti"].execution_date - timedelta(days=3)
    rs_hook = RedshiftHook('redshift')
    message = ''

    from_date = exec_date - timedelta(days = LOOKBACK_DAYS)

    netflix_visitor_query = \
                """select udate, visitors, prevdt_vistors, pct_diff from 
                    (select udate, visitors, prevdt_vistors,
                    case 
                        when prevdt_vistors = visitors then 0.00
                        when prevdt_vistors = 0 then 999999.99
                        else round((visitors - prevdt_vistors) * 100.0 / prevdt_vistors, 2) 
                        end as pct_diff from
                        (select udate, visitors, lead(visitors, 1) over(order by udate desc) as prevdt_vistors
                            from (select udate, sum(uniquevisitors) visitors from alvin_join.netflix$stream
                                    where udate::date > '{from_date}' group by udate)
                        )
                    )
                where pct_diff > {threshold} or pct_diff < -{threshold}
                order by 1 desc""".format(from_date=from_date, threshold=THRESHOLD_PERCENT)

    result = rs_hook.get_records(netflix_visitor_query)
    is_first_row = True

    for r in result:
        if is_first_row:
            logging.info('Variation in daily netflix viewership above threshold has been detected.')
            message += '\nDaily netflix viewership variation above threshold:\n\n'
            is_first_row = False

        [flag_date, visitors, prevdt_vistors, pct_diff] = r

        message += "\t{dt}: Visitors = {visitors}, Prior day's visitors = {prior}, %Change = {pct_diff}\n".format(
            dt=flag_date, visitors=visitors, prior=prevdt_vistors, pct_diff=pct_diff)

    # Send email if variation greater than threshold is found.

    if not is_first_row:
        subject = '7Park Jumpshot: QA - Large Variation in Daily Viewership'
        send_email(subject, message)
        logging.info('Failed QA check for daily variation in viewership.')
    else:
        logging.info('Passed QA check for daily variation in viewership.')

# -- end function --

# ######### Create Tasks Using Operators
create_tables = PythonOperator(
    task_id='CreateTables',
    provide_context=True,
    python_callable=create_tables,
    dag=dag)

load_tables = PythonOperator(
    task_id='LoadTables',
    provide_context=True,
    python_callable=load_tables,
    dag=dag)

join_tables = PythonOperator(
    task_id='JoinTables',
    provide_context=True,
    python_callable=join_tables,
    dag=dag)

cleanse_data = PythonOperator(
    task_id='CleanseData',
    provide_context=True,
    python_callable=cleanse_data,
    dag=dag)

qa_missing_dates = PythonOperator(
    task_id='QA-Missing-Dates',
    provide_context=True,
    python_callable=qa_check_for_missing_dates,
    dag=dag)

qa_duplicates = PythonOperator(
    task_id='QA-Duplicates',
    provide_context=True,
    python_callable=qa_check_for_duplicates,
    dag=dag)

qa_daily_visitor_count_variation = PythonOperator(
    task_id='QA-Visitor-Count-Variation',
    provide_context=True,
    python_callable=qa_check_for_variation_in_daily_unique_visitors,
    dag=dag)

# ######### Set Relations
create_tables.set_downstream(load_tables)
load_tables.set_downstream(join_tables)
join_tables.set_downstream(cleanse_data)

qa_tasklist = [qa_missing_dates, qa_duplicates, qa_daily_visitor_count_variation]

# Run the qa tasks in parallel.

for qa_task in qa_tasklist:    
    cleanse_data.set_downstream(qa_task)


