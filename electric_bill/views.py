from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClientElectricBill
from .serializers import ClientElectricBillListSerializer, ClientElectricBillDetailSerializer,\
    ClientElectricBillCreateSerializer


clafrom rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClientElectricBill
from .serializers import ClientElectricBillListSerializer, ClientElectricBillDetailSerializer,\
    ClientElectricBillCreateSerializer


class ClientElectricBillListView(APIView):
    def get(self, request):
        electric_bill = ClientElectricBill.objects.all()
        serializer = ClientElectricBillListSerializer(electric_bill, many=True)
        return Response(serializer.data)


class ClientElectricBillDetailView(APIView):
    def get(self, request, pk):
        electric_bill = ClientElectricBill.objects.get(id=pk)
        serializer = ClientElectricBillDetailSerializer(electric_bill)
        return Response(serializer.data)


class ClientElectricBillCreateView(APIView):
    def post(self, request):
        electric_bill = ClientElectricBillCreateSerializer(data=request.data)
        if electric_bill.is_valid():
            electric_bill.save()
        return Response(status=201)
