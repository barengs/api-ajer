import django_filters
from .models import Course, Category


class CourseFilter(django_filters.FilterSet):
    """Advanced filtering for courses"""
    
    # Price range filters
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    is_free = django_filters.BooleanFilter(field_name="is_free")
    
    # Category filters
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_name = django_filters.CharFilter(field_name="category__name", lookup_expr='icontains')
    
    # Course type and difficulty
    course_type = django_filters.ChoiceFilter(choices=Course.CourseType.choices)
    difficulty_level = django_filters.ChoiceFilter(choices=Course.DifficultyLevel.choices)
    
    # Rating filter
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    
    # Duration filters
    duration_min = django_filters.NumberFilter(field_name="total_duration_minutes", lookup_expr='gte')
    duration_max = django_filters.NumberFilter(field_name="total_duration_minutes", lookup_expr='lte')
    
    # Instructor filter
    instructor = django_filters.CharFilter(field_name="instructor__full_name", lookup_expr='icontains')
    
    # Featured courses
    is_featured = django_filters.BooleanFilter(field_name="is_featured")

    class Meta:
        model = Course
        fields = [
            'course_type', 'difficulty_level', 'category', 'is_free', 
            'is_featured', 'price_min', 'price_max', 'duration_min', 
            'duration_max', 'min_rating', 'instructor'
        ]

    def filter_min_rating(self, queryset, name, value):
        """Filter courses with minimum average rating"""
        from django.db.models import Avg
        return queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=value)