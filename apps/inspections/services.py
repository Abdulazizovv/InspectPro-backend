from django.db import transaction

from .models import Inspection


class InspectionService:
    @staticmethod
    @transaction.atomic
    def create(validated_data: dict, created_by) -> Inspection:
        inspection = Inspection.objects.create(
            **validated_data,
            created_by=created_by,
        )
        if inspection.status == Inspection.Status.PASSED:
            InspectionService._sync_vehicle(inspection)
        return inspection

    @staticmethod
    @transaction.atomic
    def update(inspection: Inspection, validated_data: dict) -> Inspection:
        old_status = inspection.status
        for attr, value in validated_data.items():
            setattr(inspection, attr, value)
        inspection.save()

        if inspection.status == Inspection.Status.PASSED:
            InspectionService._sync_vehicle(inspection)
        elif old_status == Inspection.Status.PASSED and inspection.status != Inspection.Status.PASSED:
            # Status passed'dan o'zgardi — vehicle'ni oldingi holatga qaytarish shart emas,
            # lekin log uchun qoldiramiz
            pass
        return inspection

    @staticmethod
    def _sync_vehicle(inspection: Inspection) -> None:
        vehicle = inspection.vehicle
        vehicle.last_inspection_date = inspection.inspection_date
        if inspection.expiry_date:
            vehicle.expiry_date = inspection.expiry_date
        vehicle.save(update_fields=["last_inspection_date", "expiry_date", "updated_at"])
