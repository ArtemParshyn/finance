from django.shortcuts import render
from rest_framework.generics import get_object_or_404

from partners.models import Partner
from partners.serializers import SerializerPartners
from rest_framework import generics, pagination, status
from rest_framework.response import Response


# Custom pagination
class StandardPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'results': data,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
        })


# Create your views here.
def partners(request):
    return render(request, template_name='partners.html')


class ModelViewListCreatePartners(generics.ListCreateAPIView):
    serializer_class = SerializerPartners
    queryset = Partner.objects.all()
    pagination_class = StandardPagination

    def get_queryset(self):
        # Added ordering by 'id' to ensure consistent pagination
        return self.queryset.filter(user=self.request.user).order_by('id')

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ModelViewRetrieveUpdateDestroyPartners(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SerializerPartners
    queryset = Partner.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        # Removed print statement for cleaner code
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        data['user'] = request.user.id
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)