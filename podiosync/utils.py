import logging
from django.conf import settings
from django.contrib import admin
from django.db import models, OperationalError, transaction, IntegrityError
from django.db import DEFAULT_DB_ALIAS, connections
from django.utils.text import slugify
from django.utils.encoding import smart_str

from dateutil import parser
import datetime
import pytz

from podiosync.api import PodioApi
from podiosync.models import ApplicationSync, PodioKey

logger = logging.getLogger(__name__)


def sync_application(app_id, api_user):
    """
    Overall function that calls all different functions in order to update a table
    The table will be created if not existing and data will be added to the table
    :param app_id: Podio application ID
    :param api_user: User to enable Podio API usage
    :return: dictionary with message
    """
    msg = {'result': 'error'}
    podio_api = PodioApi(api_user)
    app_data = get_application(app_id, podio_api)
    if app_data:
        model_fields = generate_fields(app_data['fields'])
        if model_fields:
            app_name = str(slugify(app_data['config']['name']).replace('-', '_'))
            model_to_update = create_model(app_name, fields=model_fields, app_label=getattr(settings, 'PSYNC_TABLE_PREFIX', 'psync'))
            if model_to_update:
                if modify_table(model_to_update):
                    # now we can update the data
                    items = get_application_items(app_id, podio_api)
                    if update_table(model_to_update, app_id, items):
                        msg['result'] = 'success'

    return msg


def get_application(app_id, api_object):
    try:
        app_data = api_object.auth.Application.find(app_id)
        return app_data
    except Exception as e:
        logging.error(str(e))
        return


def get_application_items(app_id, api_object, sort_desc=True):
    try:
        dict_attributes = {'limit': 500,
                           'sort_by': 'last_edit_on',
                           'sort_desc': sort_desc}
        # we create a loop to take care of the 500 limit
        app_items = []
        i = 0
        result = ['not_empty']  # adding value so we can enter the loop
        while len(result) > 0:
            dict_attributes['offset'] = i * 500  # setting the offset
            result = api_object.auth.Item.filter(int(app_id), dict_attributes)['items']
            app_items.extend(result)
            i += 1
            if len(result) < 500:
                # if we have less than 500 items, it means that we do not need to fetch again
                result = []
        return app_items
    except Exception as e:
        logging.error(str(e))
        return


def generate_fields(model_fields):
    """
    Translate the fields from podio into django model fields.
    Specific fields are handled and a catch all is set to TextField
    :param model_fields: dictionary of podio fields extracted from an application
    :return: dictionary of fields ready to generate a model or None if an error occurred
    """
    try:
        fields = {'item_id': models.IntegerField(verbose_name='Item ID',
                                                 blank=True,
                                                 null=True),
                  'date_updated': models.DateTimeField(verbose_name='Date last updated',
                                                       blank=True,
                                                       null=True)}
        for field in model_fields:
            f_type = field['type']
            f_status = field['status']
            f_label = field['label']
            f_external_id = field['external_id']
            f_required = not field['config']['required']
            # default values

            if f_status != 'deleted':
                # required flag from field is ignored as empty field were returned from podio in numerous occasions.
                # rather than entering buggus data, the fields are set to null/balnk
                f_required = True
                if f_type == 'text':
                    f_size = field['config']['settings']['size']
                    if f_size == 'small':
                        fields[f_external_id] = models.CharField(verbose_name=f_label,
                                                                 blank=f_required,
                                                                 null=f_required,
                                                                 max_length=255)
                    else:
                        fields[f_external_id] = models.TextField(verbose_name=f_label,
                                                                 blank=f_required,
                                                                 null=f_required)
                elif f_type == 'app':
                    fields[f_external_id] = models.TextField(verbose_name=f_label,
                                                             blank=f_required,
                                                             null=f_required)
                    fields['%s_ref' % f_external_id] = models.TextField(verbose_name='%s_ref' % f_label,
                                                                        blank=f_required,
                                                                        null=f_required)
                elif f_type == 'money':
                    fields[f_external_id] = models.TextField(verbose_name=f_label,
                                                             blank=f_required,
                                                             null=f_required)
                    fields['%s_currency' % f_external_id] = models.TextField(verbose_name='%s_currency' % f_label,
                                                                        blank=f_required,
                                                                        null=f_required)
                elif f_type == 'number':
                    fields[f_external_id] = models.DecimalField(verbose_name=f_label,
                                                                max_digits=20,
                                                                decimal_places=4,
                                                                blank=f_required,
                                                                null=f_required)
                elif f_type == 'date':
                    # As Dates can have a start and end, we create 2 date field
                    fields['%s' % f_external_id] = models.DateTimeField(verbose_name=f_label,
                                                                        blank=f_required,
                                                                        null=f_required)
                    # end date is not required.
                    fields['%s_end' % f_external_id] = models.DateTimeField(verbose_name=f_label,
                                                                            blank=True,
                                                                            null=True)
                else:
                    fields[f_external_id] = models.TextField(verbose_name=f_label,
                                                             blank=f_required,
                                                             null=f_required)
        return fields
    except Exception as e:
        logging.error(str(e))
        return


def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None):
    """
    Create specified model
    """
    try:
        class Meta:
            # Using type('Meta', ...) gives a dictproxy error during model creation
            pass

        if app_label:
            # app_label must be set using the Meta inner class
            setattr(Meta, 'app_label', app_label)

        # Update Meta with any options that were provided
        if options is not None:
            for key, value in options.iteritems():
                setattr(Meta, key, value)

        # Set up a dictionary to simulate declarations within a class
        attrs = {'__module__': module, 'Meta': Meta}

        # Add in any fields that were provided
        if fields:
            attrs.update(fields)

        # Create the class, which automatically triggers ModelBase processing
        model = type(name, (models.Model,), attrs)

        # Create an Admin class if admin options were provided
        if admin_opts is not None:
            class Admin(admin.ModelAdmin):
                pass
            for key, value in admin_opts:
                setattr(Admin, key, value)
            admin.site.register(model, Admin)

        return model
    except Exception as e:
        logger.error(str(e))
        return


def create_table(model_class, database=None):
    """
    Create a table using a model. If the table exist, an OperationalError is raised and we pass.
    :param model_class: The model
    :param database: The database string to use, if None default one is used
    :return: True if successful or None if not
    """
    try:
        deferred_sql = []
        if not database:
            database = DEFAULT_DB_ALIAS
        connection = connections[database]
        with connection.schema_editor() as editor:
            editor.create_model(model_class)
            deferred_sql.extend(editor.deferred_sql)
            editor.deferred_sql = []
    except OperationalError, e:
        if str(e) != 'table "%s" already exists' % model_class._meta.db_table:
            # we want to log this info and we exit
            logger.error(str(e))
            return
    except Exception as e:
        # we want to log this info and we exit
        logger.error(str(e))
        return
    return True


def modify_table(model_class, database=None):
    """
    Alter the table by adding / removing columns.
    :param model_class: the model containing the fields (columns) to use
    :param database: The database string. if None, the default one will be used.
    :return: True if successful or None if failed
    """
    if not database:
        database = DEFAULT_DB_ALIAS
    connection = connections[database]  # Create table if missing
    if model_class._meta.db_table not in connection.introspection.table_names():
        create_table(model_class, database)

    # Add field columns if missing
    table_name = model_class._meta.db_table
    fields = [(f.column, f) for f in model_class._meta.fields]
    db_column_names = [row[0] for row in connection.introspection.get_table_description(connection.cursor(), table_name)]

    for column_name, field in fields:
        if column_name not in db_column_names:
            qn = connection.ops.quote_name
            field_output = [qn(field.name), field.db_type(connection=connection)]
            field_output.append("NULL")  # we force the field to be NULL to prevent insert error
            if field.primary_key:
                field_output.append("PRIMARY KEY")
            elif field.unique:
                field_output.append("UNIQUE")
            sql_add_column = "ALTER TABLE %s ADD COLUMN %s" % (table_name, ' '.join(field_output))

            # db.add_column(table_name, column_name, field)
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql_add_column)
                except OperationalError, e:
                    # This is a big problem. we log and exit.
                    logger.critical(str(e))
                    return
    # we clean the columns (column removed)
    for column_name in db_column_names:
        try:
            dict(fields)[column_name]
        except KeyError:
            # we should delete that column
            sql_remove_column = "ALTER TABLE %s DROP COLUMN %s" % (table_name, column_name)
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql_remove_column)
                except OperationalError, e:
                    # we cannot delete the column, we just ignore this
                    logger.error(str(e))
    return True


def update_table(model_class, app_id, items, database=None):
    """
    This function update the table with data as necessary
    :param model_class: The model to use to update the DB
    :param app_id: The Application to use to retrieve the data
    :param items: The items to update the DB with
    :param database: The name of the database to use
    :return: True if successful, None if not
    """
    if not database:
        database = DEFAULT_DB_ALIAS
    # getting the last update time
    app_last_updated = pytz.utc.localize(parser.parse('1900-01-01 00:00:00'))
    try:
        app_object = ApplicationSync.objects.get(application_id=app_id)
    except ApplicationSync.DoesNotExist:
        return
    if app_object.last_synced:
        app_last_updated = app_object.last_synced
    items_updated = False
    items_counter = 0
    for item in items:
        update_item = False
        item_id = item['item_id']
        item_last_updated = pytz.utc.localize(parser.parse(item['current_revision']['created_on']))
        if item_last_updated > app_last_updated:
            update_item = True
        if update_item:
            try:
                with transaction.atomic(using=database):
                    try:
                        db_item = model_class.objects.using(database).get(item_id=item_id)
                    except model_class.DoesNotExist:
                        db_item = model_class(item_id=item_id)
                    try:
                        for field in item['fields']:
                            field_name = field['external_id']
                            field_type = field['type']
                            if field_type == 'date':
                                # we need to update the start and end
                                date_start = get_value_for_field(field)
                                date_end = get_value_for_field(field, date='end')
                                if date_start:
                                    date_start = pytz.utc.localize(date_start)
                                if date_end:
                                    date_end = pytz.utc.localize(date_end)
                                db_item.__dict__['%s' % field_name] = date_start
                                db_item.__dict__['%s_end' % field_name] = date_end
                            elif field_type == 'app':
                                # we update the field name and its reference.
                                db_item.__dict__[field_name] = get_value_for_field(field)
                                db_item.__dict__['%s_ref' % field_name] = get_value_for_field(field, app=True)
                            elif field_type == 'money':
                                # we update the field name and its reference.
                                db_item.__dict__[field_name] = get_value_for_field(field)
                                db_item.__dict__['%s_currency' % field_name] = get_value_for_field(field, extra='money')
                            else:
                                db_item.__dict__[field_name] = get_value_for_field(field)
                            db_item.date_updated = pytz.utc.localize(datetime.datetime.now())
                        db_item.save(using=database)
                    except Exception as e:
                        logger.error(str(e))
                        return
                items_updated = True
                items_counter += 1
            except IntegrityError, e:
                logger.error(str(e))
                return
    if items_updated:
        logger.info('%s items updated for table: %s' % (items_counter,
                                                       model_class._meta.db_table))
    app_object.last_synced = pytz.utc.localize(datetime.datetime.now())
    app_object.save()
    logger.info('Table %s synchronised (app_id: %s, app_name: %s)' % (model_class._meta.db_table,
                                                                      app_id,
                                                                      app_object.application_name))
    return True


def get_value_for_field(field, prof_id=False, date=None, app=False, extra=None):
    """
    .. function::

        :description: retrieve the value for a field from podio item
        :param field: This is a field from an item, it should contain all data
        :param prof_id: (True/False). to be set to true if the field needs to be considered as a 'Contact' field
        :param date: (end/None). if set to 'end' we will extract the end date from the field. None will get the start date
        :param app: (True/False). If set to True, the value returned is the item_id rather than the string
        :rtype: a string containing the field's value
        :raises:

    """

    field_type = field['type']
    value = ''
    try:
        if field_type == 'date':
            if date == 'end':
                if 'end' in field['values'][0]:
                    value = parser.parse(field['values'][0]['end'])
                else:
                    value = None
            else:
                value = parser.parse(field['values'][0]['start'])

        elif field_type == 'text':
            value = smart_str(field['values'][0]['value'])
        elif field_type == 'number':
            value = [smart_str(val['value']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'progress':
            value = [smart_str(val['value']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'category':
            value = [smart_str(val['value']['text']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'email':
            value = [smart_str(val['value']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'phone':
            value = [smart_str(val['value']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'money':
            if extra == 'money':
                value = smart_str(field['values'][0]['currency'])
            else:
                value = smart_str(field['values'][0]['value'])
        elif field_type == 'duration':
            value = [smart_str(val['value']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'contact':
            if prof_id:
                value = [int(val['value']['profile_id']) for val in field['values']]
            else:
                value = [smart_str(val['value']['name']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'app':
            if not app:
                value = [smart_str(val['value']['title']) for val in field['values']]
            else:
                value = [int(val['value']['item_id']) for val in field['values']]
            value = ', '.join(map(str, value))
        elif field_type == 'image':
            value = field['values'][0]['value']['link']
        elif field_type == 'location':
            value = field['values'][0]['formatted']
    except Exception as e:
        logger.error(str(e))

    if isinstance(value, str):
        value = value.decode('utf-8')
    return value


def get_app_details(app_id, podio_key_id):
    podio_key = PodioKey.objects.get(id=podio_key_id)
    podio_api = PodioApi(podio_key.podio_user.user_name)
    return get_application(app_id, podio_api)
