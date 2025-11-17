import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_execption_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

logger = logging.getLogger('template')


def exception_handler(exc, context):
    """
    自定义异常捕获
    :param exc:异常对象
    :param context:抛出上下文(request,view)
    """
    response = drf_execption_handler(exc, context)  # django的异常捕获

    if response:
        # DRF的异常，统一返回格式
        if isinstance(exc, (DRFValidationError, DjangoValidationError)):
            if hasattr(exc, 'detail'):
                detail = exc.detail
                if isinstance(detail, dict):
                    # 如果是字典格式，取第一个错误信息
                    first_key = next(iter(detail))
                    first_value = detail[first_key]
                    if isinstance(first_value, list) and first_value:
                        error_message = str(first_value[0])
                    else:
                        error_message = str(first_value)
                elif isinstance(detail, list) and detail:
                    error_message = str(detail[0])
                else:
                    error_message = str(detail)

                response.data = {"detail": error_message}
                return response

        if hasattr(response, 'data') and response.data:
            if isinstance(response.data, dict):
                if 'detail' not in response.data:
                    error_message = None
                    if 'message' in response.data:
                        error_message = response.data['message']
                    elif 'error' in response.data:
                        error_message = response.data['error']
                    elif 'non_field_errors' in response.data:
                        non_field_errors = response.data['non_field_errors']
                        if isinstance(non_field_errors, list) and non_field_errors:
                            error_message = str(non_field_errors[0])
                        else:
                            error_message = str(non_field_errors)
                    else:
                        # 若无明确的错误字段，使用第一个值
                        first_key = next(iter(response.data))
                        first_value = response.data[first_key]
                        if isinstance(first_value, list) and first_value:
                            error_message = str(first_value[0])
                        else:
                            error_message = str(first_value)

                    if error_message:
                        response.data = {"detail": error_message}

    if not response:  # 如果捕获不到，再次判断是否为数据库异常，并捕获
        view = context.get('view')
        if isinstance(exc, DatabaseError):
            logger.error(f'[{view}]{exc}')
            response = Response({'detail': "数据库异常"}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
        else:
            logger.error(f'[{view}]未捕获的异常: {exc}')
            response = Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
