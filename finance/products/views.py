from django.shortcuts import render
from rest_framework import generics, pagination, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from products.models import Product
from products.serializers import SerializerProducts


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


def products(request):
    return render(request, template_name='products.html')


class ModelViewListCreateProducts(generics.ListCreateAPIView):
    serializer_class = SerializerProducts
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтрация по текущему пользователю
        return Product.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Автоматическое назначение текущего пользователя
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data
        data['user'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ModelViewRetrieveUpdateDestroyProducts(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SerializerProducts
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтрация по текущему пользователю
        return Product.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        print(pk)
        if not pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        data['user'] = request.user.id
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)
