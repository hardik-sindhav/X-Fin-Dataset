"""
Request Validation Schemas using Marshmallow
Provides validation for all API endpoints
"""

from marshmallow import Schema, fields, validate, ValidationError, validates
from datetime import datetime


class PaginationSchema(Schema):
    """Schema for pagination parameters"""
    page = fields.Int(
        missing=1,
        validate=validate.Range(min=1, max=10000),
        error_messages={
            'invalid': 'Page must be a valid integer',
            'required': 'Page is required'
        }
    )
    limit = fields.Int(
        missing=15,
        validate=validate.Range(min=1, max=100),
        error_messages={
            'invalid': 'Limit must be a valid integer between 1 and 100',
            'required': 'Limit is required'
        }
    )


class DateFilterSchema(Schema):
    """Schema for date filtering parameters"""
    start_date = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$'),
        error_messages={
            'invalid': 'start_date must be in YYYY-MM-DD format'
        }
    )
    end_date = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$'),
        error_messages={
            'invalid': 'end_date must be in YYYY-MM-DD format'
        }
    )
    
    @validates('start_date')
    def validate_start_date_format(self, value):
        """Validate that start_date is a valid date"""
        if value:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('start_date must be a valid date in YYYY-MM-DD format')
    
    @validates('end_date')
    def validate_end_date_format(self, value):
        """Validate that end_date is a valid date and after start_date"""
        if value:
            try:
                end_dt = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValidationError('end_date must be a valid date in YYYY-MM-DD format')
            
            # Check if end_date is after start_date
            if hasattr(self, 'context') and self.context:
                start_date_str = self.context.get('start_date')
                if start_date_str:
                    try:
                        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        if end_dt < start_dt:
                            raise ValidationError('end_date must be after or equal to start_date')
                    except ValueError:
                        pass  # start_date validation will catch this


class LoginSchema(Schema):
    """Schema for login request"""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100),
        error_messages={
            'required': 'Username is required',
            'invalid': 'Username must be a string'
        }
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200),
        error_messages={
            'required': 'Password is required',
            'invalid': 'Password must be a string'
        }
    )


class SchedulerConfigSchema(Schema):
    """Schema for scheduler configuration updates"""
    scheduler_type = fields.Str(
        required=True,
        validate=validate.OneOf(['banks', 'indices', 'gainers_losers', 'news', 'fiidii']),
        error_messages={
            'required': 'scheduler_type is required',
            'invalid': 'scheduler_type must be one of: banks, indices, gainers_losers, news, fiidii'
        }
    )
    config = fields.Dict(
        required=True,
        error_messages={
            'required': 'config is required',
            'invalid': 'config must be a dictionary'
        }
    )


class ConfigUpdateSchema(Schema):
    """Schema for individual config field updates"""
    interval_minutes = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=1440),  # 1 minute to 24 hours
        error_messages={
            'invalid': 'interval_minutes must be between 1 and 1440'
        }
    )
    start_time = fields.Str(
        required=False,
        validate=validate.Regexp(r'^\d{2}:\d{2}$'),
        error_messages={
            'invalid': 'start_time must be in HH:MM format (e.g., 09:15)'
        }
    )
    end_time = fields.Str(
        required=False,
        validate=validate.Regexp(r'^\d{2}:\d{2}$'),
        error_messages={
            'invalid': 'end_time must be in HH:MM format (e.g., 15:30)'
        }
    )
    enabled = fields.Bool(
        required=False,
        error_messages={
            'invalid': 'enabled must be a boolean'
        }
    )
    
    @validates('end_time')
    def validate_end_after_start(self, value):
        """Validate that end_time is after start_time"""
        if value and 'start_time' in self.context and self.context.get('start_time'):
            start = datetime.strptime(self.context['start_time'], '%H:%M').time()
            end = datetime.strptime(value, '%H:%M').time()
            if end <= start:
                raise ValidationError('end_time must be after start_time')
    
    @validates('start_time')
    def validate_start_before_end(self, value):
        """Validate that start_time is before end_time"""
        if value and 'end_time' in self.context and self.context.get('end_time'):
            start = datetime.strptime(value, '%H:%M').time()
            end = datetime.strptime(self.context['end_time'], '%H:%M').time()
            if end <= start:
                raise ValidationError('start_time must be before end_time')


class HolidaySchema(Schema):
    """Schema for holiday date"""
    date = fields.Str(
        required=True,
        validate=validate.Regexp(r'^\d{4}-\d{2}-\d{2}$'),
        error_messages={
            'required': 'date is required',
            'invalid': 'date must be in YYYY-MM-DD format'
        }
    )
    
    @validates('date')
    def validate_date_format(self, value):
        """Validate that the date string is a valid date"""
        if value:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise ValidationError('date must be a valid date in YYYY-MM-DD format')


class RecordIdSchema(Schema):
    """Schema for record ID validation"""
    record_id = fields.Str(
        required=True,
        validate=validate.Length(min=24, max=24),
        error_messages={
            'required': 'record_id is required',
            'invalid': 'record_id must be a valid MongoDB ObjectId (24 characters)'
        }
    )


class CombinedPaginationDateSchema(PaginationSchema, DateFilterSchema):
    """Combined schema for endpoints that use both pagination and date filtering"""
    pass

