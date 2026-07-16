class BranchScopedQuerysetMixin:
    """
    Barcha ViewSet'larda foydalaniladigan mixin.
    super_admin: hamma ko'radi (yoki ?branch= query param bo'yicha filtr)
    branch_admin/operator: faqat o'z filiali

    MUHIM: Subclass o'zining get_queryset()ini super().get_queryset() orqali chaqirishi kerak.
    """

    def _apply_branch_filter(self, qs):
        user = self.request.user
        if user.role == "super_admin":
            branch_id = self.request.query_params.get("branch")
            if branch_id:
                return qs.filter(branch_id=branch_id)
            return qs
        return qs.filter(branch=user.branch)

    def get_queryset(self):
        qs = super().get_queryset()
        return self._apply_branch_filter(qs)

    def perform_create(self, serializer):
        user = self.request.user
        branch = getattr(user, "branch", None)
        if user.role == "super_admin":
            branch_id = self.request.data.get("branch") or self.request.query_params.get("branch")
            if branch_id:
                from apps.branches.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id)
                except Branch.DoesNotExist:
                    branch = None
        serializer.save(branch=branch, created_by=user)
