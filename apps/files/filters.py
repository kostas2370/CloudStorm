from django_filters import rest_framework as filters
from .models import File
from django.contrib.postgres.search import SearchVector


class FileFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains", label="File Name (partial)")
    short_description = filters.CharFilter(
        lookup_expr="icontains", label="Short Description (partial)"
    )
    file_type = filters.CharFilter(lookup_expr="exact", label="File Type")
    group = filters.UUIDFilter(field_name="group__id", label="Group ID")
    uploaded_by = filters.UUIDFilter(field_name="uploaded_by__id", label="Uploader ID")

    keywords = filters.CharFilter(
        method="full_text_search", label="Full Text Search in Extracted Data"
    )

    class Meta:
        model = File
        fields = [
            "name",
            "short_description",
            "file_type",
            "group",
            "uploaded_by",
            "keywords",
        ]

    def full_text_search(self, queryset, name, value):
        return (
            queryset.annotate(
                search_vector=(
                    SearchVector("name", weight="A", config="english")
                    + SearchVector("short_description", weight="B", config="english")
                    + SearchVector("extracted_data__data", weight="C", config="english")
                )
            )
            .filter(search_vector=value)
            .distinct()
        )
