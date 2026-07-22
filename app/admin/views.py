from starlette_admin.contrib.sqla import ModelView


class AnimalAdmin(ModelView):
    searchable_fields = ["name"]


class HealthLogAdmin(ModelView):
    searchable_fields = ["procedure_name"]


class UserAdmin(ModelView):
    searchable_fields = ["name"]
