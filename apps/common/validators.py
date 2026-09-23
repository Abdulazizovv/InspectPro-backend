from rest_framework import serializers


def validate_same_branch(request, obj, field_label: str = "obyekt"):
    """
    Berilgan `obj` (branch FK'ga ega model instansi) request.user bilan bir xil
    filialga tegishli ekanligini tekshiradi. super_admin uchun cheklov yo'q.

    Operator/branch_admin boshqa filialga tegishli FK (client, vehicle,
    inspection, inspector va h.k.) ni yozuvga bog'lay olmasligi kerak —
    aks holda cross-branch data leakage/yozuv yuz beradi.
    """
    if obj is None or request is None:
        return obj
    user = getattr(request, "user", None)
    if user is None or getattr(user, "role", None) == "super_admin":
        return obj
    obj_branch_id = getattr(obj, "branch_id", None)
    user_branch_id = getattr(user, "branch_id", None)
    if obj_branch_id != user_branch_id:
        raise serializers.ValidationError(
            f"Boshqa filialga tegishli {field_label}ni tanlash mumkin emas."
        )
    return obj
