import csv
from datetime import datetime
from io import StringIO

from django.db import connection
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (
    EducationCohortApplication,
    Member,
    Project,
    ProjectApplication,
    ResearchCohortApplication,
)
from .serializers import (
    EducationCohortApplicationCreateSerializer,
    EducationCohortApplicationSerializer,
    MemberSerializer,
    ProjectApplicationSerializer,
    ProjectSerializer,
    ResearchCohortApplicationCreateSerializer,
    ResearchCohortApplicationSerializer,
)


class DatabaseGuardMixin:
    """Return 503 if we are not on Postgres (e.g., local sqlite dev)."""

    def _db_is_sqlite(self) -> bool:
        return "sqlite" in connection.vendor

    def list(self, request, *args, **kwargs):  # type: ignore
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):  # type: ignore
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)
        return super().retrieve(request, *args, **kwargs)


class ProjectViewSet(DatabaseGuardMixin, viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by("-created_at")
    serializer_class = ProjectSerializer
    filterset_fields = {
        "status": ["exact", "in"],
        "project_type": ["exact", "in"],
        "priority": ["exact", "in"],
    }
    search_fields = ["title", "description", "objectives", "deliverables"]
    ordering_fields = ["created_at", "title", "launch_date", "priority"]
    ordering = ["-created_at"]

    def get_permissions(self):  # type: ignore
        # Allow public read access, but require admin for write operations
        if self.action in ["list", "retrieve", "export"]:
            # Export can be public (filtered data)
            return [AllowAny()]
        # Import here to avoid circular dependency
        from apps.users.permissions import IsAdmin
        return [IsAdmin()]

    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """Bulk update multiple projects"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        project_ids = request.data.get('project_ids', [])
        update_data = request.data.get('update_data', {})

        if not project_ids or not update_data:
            return Response(
                {"error": "Both project_ids and update_data are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update projects
        updated_count = Project.objects.filter(id__in=project_ids).update(**update_data)

        return Response({
            "detail": f"Successfully updated {updated_count} projects",
            "updated_count": updated_count
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export projects to CSV"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        # Apply same filters as list view
        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Title', 'Description', 'Status', 'Location', 'Launch Date',
            'Project Type', 'Participants Count', 'Max Participants',
            'Objectives', 'Deliverables', 'Focal Person Name', 'Focal Person Email',
            'Priority', 'Human Skills Required', 'Platform Requirements',
            'Timeline Start', 'Timeline End', 'Budget Estimate', 'Current Budget',
            'Is Concurrent', 'Created At'
        ])

        # Write data
        for project in queryset:
            writer.writerow([
                project.id,
                project.title,
                project.description or '',
                project.status or '',
                project.location or '',
                project.launch_date or '',
                project.project_type or '',
                project.participants_count or 0,
                project.max_participants or 0,
                project.objectives or '',
                project.deliverables or '',
                project.focal_person_name or '',
                project.focal_person_email or '',
                project.priority or '',
                project.human_skills_required or '',
                project.platform_requirements or '',
                project.timeline_start or '',
                project.timeline_end or '',
                project.budget_estimate or '',
                project.current_budget or '',
                project.is_concurrent,
                project.created_at
            ])

        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="projects_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """Get project analytics"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count, Sum, Avg

        queryset = Project.objects.all()

        analytics_data = {
            "total_projects": queryset.count(),
            "by_status": dict(queryset.values_list('status').annotate(count=Count('id'))),
            "by_type": dict(queryset.values_list('project_type').annotate(count=Count('id'))),
            "by_priority": dict(queryset.values_list('priority').annotate(count=Count('id'))),
            "total_participants": queryset.aggregate(Sum('participants_count'))['participants_count__sum'] or 0,
            "avg_participants": queryset.aggregate(Avg('participants_count'))['participants_count__avg'] or 0,
            "total_budget_estimate": float(queryset.aggregate(Sum('budget_estimate'))['budget_estimate__sum'] or 0),
            "total_current_budget": float(queryset.aggregate(Sum('current_budget'))['current_budget__sum'] or 0),
            "concurrent_projects": queryset.filter(is_concurrent=True).count(),
        }

        return Response(analytics_data)


class MemberViewSet(DatabaseGuardMixin, mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Member.objects.all().order_by("-created_at")
    serializer_class = MemberSerializer
    permission_classes = [AllowAny]  # Allow public member registration
    search_fields = ["name", "email", "skills", "areaOfExpertise", "occupation"]
    filterset_fields = ["country", "city", "membershiptype", "is_active", "gender"]

    def create(self, request, *args, **kwargs):
        """Create a new member with proper UUID handling"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)
        
        # Import uuid here to avoid circular imports
        import uuid
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get the data and ensure we don't pass 'id'
        data = request.data.copy()
        
        # Log the incoming data for debugging
        logger.info(f"Received member application data: {data}")
        
        # Remove id if present (will be auto-generated by DB)
        data.pop('id', None)
        
        # Ensure required fields are present
        required_fields = ['name', 'email', 'phone', 'gender', 'membershiptype']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create serializer with the data
        serializer = self.get_serializer(data=data)
        
        try:
            serializer.is_valid(raise_exception=True)
            
            # Create the member instance but don't save yet
            member = Member(
                id=uuid.uuid4(),  # Generate UUID explicitly
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone'),
                gender=data.get('gender'),
                membershiptype=data.get('membershiptype'),
                country=data.get('country'),
                city=data.get('city'),
                linkedin=data.get('linkedin'),
                experience=data.get('experience'),
                areaOfExpertise=data.get('areaOfExpertise'),
                school=data.get('school'),
                level=data.get('level'),
                occupation=data.get('occupation'),
                jobtitle=data.get('jobtitle'),
                industry=data.get('industry'),
                major=data.get('major'),
                skills=data.get('skills'),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_active=True
            )
            member.save()
            
            # Serialize the created member for response
            response_serializer = self.get_serializer(member)
            headers = self.get_success_headers(response_serializer.data)
            
            logger.info(f"Successfully created member: {member.email}")
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            logger.error(f"Error creating member: {str(e)}")
            logger.error(f"Serializer errors: {serializer.errors if hasattr(serializer, 'errors') else 'N/A'}")
            return Response(
                {
                    "error": str(e),
                    "details": serializer.errors if hasattr(serializer, 'errors') else {}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='verify', permission_classes=[AllowAny])
    def verify_email(self, request):
        """Verify if an email is registered as a member"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Email parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = Member.objects.get(email__iexact=email.lower())
            return Response({
                "exists": True,
                "member": MemberSerializer(member).data
            })
        except Member.DoesNotExist:
            return Response({"exists": False})

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export members to CSV"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        # Apply same filters as list view
        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Name', 'Email', 'Phone', 'Country', 'City', 'LinkedIn',
            'Experience', 'Area of Expertise', 'School', 'Level', 'Occupation',
            'Job Title', 'Industry', 'Major', 'Gender', 'Membership Type',
            'Skills', 'Is Active', 'Created At'
        ])

        # Write data
        for member in queryset:
            writer.writerow([
                str(member.id),
                member.name,
                member.email,
                member.phone or '',
                member.country or '',
                member.city or '',
                member.linkedin or '',
                member.experience or '',
                member.areaOfExpertise or '',
                member.school or '',
                member.level or '',
                member.occupation or '',
                member.jobtitle or '',
                member.industry or '',
                member.major or '',
                member.gender,
                member.membershiptype,
                member.skills or '',
                member.is_active,
                member.created_at
            ])

        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="members_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='locations')
    def member_locations(self, request):
        """Get member locations grouped by country for world map visualization"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count
        from collections import defaultdict

        # Get all members with country information
        members = Member.objects.filter(
            country__isnull=False,
            is_active=True
        ).exclude(country='').order_by('country')

        # Group members by country
        locations_by_country = defaultdict(list)
        for member in members:
            country = member.country.strip() if member.country else None
            if country:
                locations_by_country[country].append({
                    'id': str(member.id),
                    'name': member.name,
                    'email': member.email,
                    'city': member.city,
                    'membershipType': member.membershiptype,
                    'gender': member.gender,
                    'occupation': member.occupation,
                    'industry': member.industry,
                })

        # Format the response
        locations = [
            {
                'country': country,
                'count': len(members_list),
                'members': members_list
            }
            for country, members_list in locations_by_country.items()
        ]

        # Sort by count (descending)
        locations.sort(key=lambda x: x['count'], reverse=True)

        return Response({
            'total_members': members.count(),
            'total_countries': len(locations),
            'locations': locations
        })

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """Get member analytics"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count

        queryset = Member.objects.all()

        analytics_data = {
            "total_members": queryset.count(),
            "active_members": queryset.filter(is_active=True).count(),
            "by_country": dict(queryset.values_list('country').annotate(count=Count('id')).order_by('-count')[:10]),
            "by_city": dict(queryset.values_list('city').annotate(count=Count('id')).order_by('-count')[:10]),
            "by_membership_type": dict(queryset.values_list('membershiptype').annotate(count=Count('id'))),
            "by_gender": dict(queryset.values_list('gender').annotate(count=Count('id'))),
            "by_experience": dict(queryset.values_list('experience').annotate(count=Count('id'))),
            "by_industry": dict(queryset.values_list('industry').annotate(count=Count('id')).order_by('-count')[:10]),
        }

        return Response(analytics_data)


class ProjectApplicationViewSet(
    DatabaseGuardMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = ProjectApplication.objects.all().order_by("-applied_date")
    serializer_class = ProjectApplicationSerializer
    filterset_fields = ["project_id", "status"]
    search_fields = ["applicant_name", "applicant_email", "skills", "motivation"]

    def get_permissions(self):  # type: ignore
        # Allow public read and create, require admin for updates
        if self.action in ["list", "retrieve", "create", "check_existing", "export"]:
            return [AllowAny()]
        from apps.users.permissions import IsAdmin
        return [IsAdmin()]

    def perform_create(self, serializer):  # type: ignore
        # For anonymous applications, use provided data directly
        if not self.request.user.is_authenticated:
            serializer.save(applied_date=timezone.now())
            return

        # Auto-set applicant fields if not provided for authenticated users
        user = self.request.user
        data = {
            "applicant_name": getattr(user, "first_name", "") or "Anonymous",
            "applicant_email": getattr(user, "email", ""),
        }
        for k, v in data.items():
            if k not in serializer.validated_data or not serializer.validated_data.get(k):
                serializer.validated_data[k] = v
        serializer.save(applied_date=timezone.now())

    @action(detail=False, methods=['get'], url_path='check', permission_classes=[AllowAny])
    def check_existing(self, request):
        """Check if an application already exists for a project and email"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        project_id = request.query_params.get('project_id')
        email = request.query_params.get('email')

        if not project_id or not email:
            return Response(
                {"error": "Both project_id and email parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            application = ProjectApplication.objects.get(
                project_id=project_id,
                applicant_email__iexact=email.lower()
            )
            return Response({
                "exists": True,
                "application": ProjectApplicationSerializer(application).data
            })
        except ProjectApplication.DoesNotExist:
            return Response({"exists": False})

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        """Bulk approve multiple applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Bulk approved')

        if not application_ids:
            return Response(
                {"error": "application_ids is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update applications
        updated_count = ProjectApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='approved',
            reviewed_date=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully approved {updated_count} applications",
            "updated_count": updated_count
        })

    @action(detail=False, methods=['post'], url_path='bulk-reject')
    def bulk_reject(self, request):
        """Bulk reject multiple applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Bulk rejected')

        if not application_ids:
            return Response(
                {"error": "application_ids is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update applications
        updated_count = ProjectApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='rejected',
            reviewed_date=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully rejected {updated_count} applications",
            "updated_count": updated_count
        })

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export applications to CSV"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        # Apply same filters as list view
        queryset = self.filter_queryset(self.get_queryset())

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Project ID', 'Applicant Name', 'Applicant Email',
            'Skills', 'Motivation', 'Status', 'Applied Date', 'Reviewed Date',
            'Reviewer Notes', 'Created At'
        ])

        # Write data
        for app in queryset:
            writer.writerow([
                str(app.id),
                app.project_id,
                app.applicant_name,
                app.applicant_email,
                app.skills or '',
                app.motivation or '',
                app.status or '',
                app.applied_date or '',
                app.reviewed_date or '',
                app.reviewer_notes or '',
                app.created_at
            ])

        # Create response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="applications_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """Get application analytics"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count

        queryset = ProjectApplication.objects.all()

        analytics_data = {
            "total_applications": queryset.count(),
            "by_status": dict(queryset.values_list('status').annotate(count=Count('id'))),
            "by_project": dict(queryset.values_list('project_id').annotate(count=Count('id'))),
            "pending_count": queryset.filter(status='pending').count(),
            "approved_count": queryset.filter(status='approved').count(),
            "rejected_count": queryset.filter(status='rejected').count(),
        }

        return Response(analytics_data)

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """Send email to a specific applicant"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application = self.get_object()
        subject = request.data.get('subject')
        message = request.data.get('message')

        if not subject or not message:
            return Response(
                {"error": "Both subject and message are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Send email asynchronously
        from apps.platform.tasks import send_applicant_email
        send_applicant_email.delay(
            applicant_email=application.applicant_email,
            applicant_name=application.applicant_name,
            subject=subject,
            message=message
        )

        return Response({"detail": "Email queued for sending"})


class ResearchCohortApplicationViewSet(
    DatabaseGuardMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Research Cohort Applications.

    - POST /apply/ - Submit application (requires email verification against members table)
    - GET /verify-email/ - Check if email exists in members table
    - GET / - List all applications (admin only)
    - GET /{id}/ - Get application detail
    - PATCH /{id}/ - Update application (admin only)
    """
    queryset = ResearchCohortApplication.objects.all().order_by("-applied_at")
    serializer_class = ResearchCohortApplicationSerializer
    filterset_fields = ["status", "cohort_batch"]
    search_fields = ["name", "email", "research_interest", "research_topic"]

    def get_permissions(self):
        if self.action in ["apply", "verify_email", "check_existing"]:
            return [AllowAny()]
        if self.action in ["list", "retrieve", "export", "analytics"]:
            return [AllowAny()]
        from apps.users.permissions import IsAdmin
        return [IsAdmin()]

    @action(detail=False, methods=['get'], url_path='verify-email', permission_classes=[AllowAny])
    def verify_email(self, request):
        """
        Verify if an email is registered as a member.
        Must be a member first before applying to cohort.
        """
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        email = request.query_params.get('email')
        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = Member.objects.get(email__iexact=email.lower())
            return Response({
                "exists": True,
                "is_member": True,
                "member": {
                    "id": str(member.id),
                    "name": member.name,
                    "email": member.email,
                    "phone": member.phone,
                },
                "message": "Email is registered. You can proceed with the application."
            })
        except Member.DoesNotExist:
            return Response({
                "exists": False,
                "is_member": False,
                "message": "Email not found. Please register as a member first before applying to the cohort."
            })

    @action(detail=False, methods=['get'], url_path='check', permission_classes=[AllowAny])
    def check_existing(self, request):
        """Check if an application already exists for this email and cohort batch"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        email = request.query_params.get('email')
        cohort_batch = request.query_params.get('cohort_batch')

        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = ResearchCohortApplication.objects.filter(email__iexact=email.lower())
        if cohort_batch:
            queryset = queryset.filter(cohort_batch=cohort_batch)

        if queryset.exists():
            application = queryset.first()
            return Response({
                "exists": True,
                "application": ResearchCohortApplicationSerializer(application).data
            })
        return Response({"exists": False})

    @action(detail=False, methods=['post'], url_path='apply', permission_classes=[AllowAny])
    def apply(self, request):
        """
        Submit a research cohort application.
        First verifies that the email exists in the members table.
        If email is not a member, returns error asking them to register first.
        """
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        serializer = ResearchCohortApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower()

        # Step 1: Verify email exists in members table
        try:
            member = Member.objects.get(email__iexact=email)
        except Member.DoesNotExist:
            return Response({
                "error": "not_a_member",
                "message": "Email not found in our member database. Please register as a member first before applying to the research cohort.",
                "register_url": "/signup"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Check if already applied for this cohort batch
        cohort_batch = serializer.validated_data.get('cohort_batch')
        existing_query = ResearchCohortApplication.objects.filter(
            email__iexact=email
        )
        if cohort_batch:
            existing_query = existing_query.filter(cohort_batch=cohort_batch)

        if existing_query.exists():
            return Response({
                "error": "already_applied",
                "message": "You have already submitted an application for this cohort.",
                "application": ResearchCohortApplicationSerializer(existing_query.first()).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Create the application
        application = ResearchCohortApplication.objects.create(
            member_id=member.id,
            email=email,
            name=member.name,
            phone=member.phone,
            research_interest=serializer.validated_data['research_interest'],
            research_topic=serializer.validated_data.get('research_topic', ''),
            research_experience=serializer.validated_data.get('research_experience', ''),
            academic_background=serializer.validated_data.get('academic_background', ''),
            current_institution=serializer.validated_data.get('current_institution', ''),
            highest_qualification=serializer.validated_data.get('highest_qualification', ''),
            field_of_study=serializer.validated_data.get('field_of_study', ''),
            publications=serializer.validated_data.get('publications', ''),
            skills=serializer.validated_data.get('skills', ''),
            motivation=serializer.validated_data['motivation'],
            availability=serializer.validated_data.get('availability', ''),
            preferred_research_area=serializer.validated_data.get('preferred_research_area', ''),
            cohort_batch=cohort_batch,
            status='pending',
            applied_at=timezone.now(),
        )

        return Response({
            "success": True,
            "message": "Application submitted successfully!",
            "application": ResearchCohortApplicationSerializer(application).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export research cohort applications to CSV"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        queryset = self.filter_queryset(self.get_queryset())

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 'Name', 'Email', 'Phone', 'Research Interest', 'Research Topic',
            'Research Experience', 'Academic Background', 'Current Institution',
            'Highest Qualification', 'Field of Study', 'Publications', 'Skills',
            'Motivation', 'Availability', 'Preferred Research Area', 'Status',
            'Cohort Batch', 'Applied At', 'Reviewed At', 'Reviewer Notes'
        ])

        for app in queryset:
            writer.writerow([
                str(app.id), app.name, app.email, app.phone or '',
                app.research_interest, app.research_topic or '',
                app.research_experience or '', app.academic_background or '',
                app.current_institution or '', app.highest_qualification or '',
                app.field_of_study or '', app.publications or '', app.skills or '',
                app.motivation, app.availability or '', app.preferred_research_area or '',
                app.status, app.cohort_batch or '', app.applied_at, app.reviewed_at or '',
                app.reviewer_notes or ''
            ])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="research_cohort_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """Get research cohort application analytics"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count

        queryset = ResearchCohortApplication.objects.all()

        return Response({
            "total_applications": queryset.count(),
            "by_status": dict(queryset.values_list('status').annotate(count=Count('id'))),
            "by_cohort_batch": dict(queryset.values_list('cohort_batch').annotate(count=Count('id'))),
            "pending_count": queryset.filter(status='pending').count(),
            "approved_count": queryset.filter(status='approved').count(),
            "rejected_count": queryset.filter(status='rejected').count(),
        })

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        """Bulk approve research cohort applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Approved')

        if not application_ids:
            return Response({"error": "application_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = ResearchCohortApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='approved',
            reviewed_at=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully approved {updated_count} applications",
            "updated_count": updated_count
        })

    @action(detail=False, methods=['post'], url_path='bulk-reject')
    def bulk_reject(self, request):
        """Bulk reject research cohort applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Rejected')

        if not application_ids:
            return Response({"error": "application_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = ResearchCohortApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully rejected {updated_count} applications",
            "updated_count": updated_count
        })


class EducationCohortApplicationViewSet(
    DatabaseGuardMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Education Cohort Applications.

    - POST /apply/ - Submit application (requires email verification against members table)
    - GET /verify-email/ - Check if email exists in members table
    - GET / - List all applications (admin only)
    - GET /{id}/ - Get application detail
    - PATCH /{id}/ - Update application (admin only)
    """
    queryset = EducationCohortApplication.objects.all().order_by("-applied_at")
    serializer_class = EducationCohortApplicationSerializer
    filterset_fields = ["status", "cohort_batch"]
    search_fields = ["name", "email", "education_interest", "field_of_study"]

    def get_permissions(self):
        if self.action in ["apply", "verify_email", "check_existing"]:
            return [AllowAny()]
        if self.action in ["list", "retrieve", "export", "analytics"]:
            return [AllowAny()]
        from apps.users.permissions import IsAdmin
        return [IsAdmin()]

    @action(detail=False, methods=['get'], url_path='verify-email', permission_classes=[AllowAny])
    def verify_email(self, request):
        """
        Verify if an email is registered as a member.
        Must be a member first before applying to cohort.
        """
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        email = request.query_params.get('email')
        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            member = Member.objects.get(email__iexact=email.lower())
            return Response({
                "exists": True,
                "is_member": True,
                "member": {
                    "id": str(member.id),
                    "name": member.name,
                    "email": member.email,
                    "phone": member.phone,
                },
                "message": "Email is registered. You can proceed with the application."
            })
        except Member.DoesNotExist:
            return Response({
                "exists": False,
                "is_member": False,
                "message": "Email not found. Please register as a member first before applying to the cohort."
            })

    @action(detail=False, methods=['get'], url_path='check', permission_classes=[AllowAny])
    def check_existing(self, request):
        """Check if an application already exists for this email and cohort batch"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        email = request.query_params.get('email')
        cohort_batch = request.query_params.get('cohort_batch')

        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = EducationCohortApplication.objects.filter(email__iexact=email.lower())
        if cohort_batch:
            queryset = queryset.filter(cohort_batch=cohort_batch)

        if queryset.exists():
            application = queryset.first()
            return Response({
                "exists": True,
                "application": EducationCohortApplicationSerializer(application).data
            })
        return Response({"exists": False})

    @action(detail=False, methods=['post'], url_path='apply', permission_classes=[AllowAny])
    def apply(self, request):
        """
        Submit an education cohort application.
        First verifies that the email exists in the members table.
        If email is not a member, returns error asking them to register first.
        """
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        serializer = EducationCohortApplicationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower()

        # Step 1: Verify email exists in members table
        try:
            member = Member.objects.get(email__iexact=email)
        except Member.DoesNotExist:
            return Response({
                "error": "not_a_member",
                "message": "Email not found in our member database. Please register as a member first before applying to the education cohort.",
                "register_url": "/signup"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Check if already applied for this cohort batch
        cohort_batch = serializer.validated_data.get('cohort_batch')
        existing_query = EducationCohortApplication.objects.filter(
            email__iexact=email
        )
        if cohort_batch:
            existing_query = existing_query.filter(cohort_batch=cohort_batch)

        if existing_query.exists():
            return Response({
                "error": "already_applied",
                "message": "You have already submitted an application for this cohort.",
                "application": EducationCohortApplicationSerializer(existing_query.first()).data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Step 3: Create the application
        application = EducationCohortApplication.objects.create(
            member_id=member.id,
            email=email,
            name=member.name,
            phone=member.phone,
            education_interest=serializer.validated_data['education_interest'],
            current_education_level=serializer.validated_data.get('current_education_level', ''),
            target_education_level=serializer.validated_data.get('target_education_level', ''),
            current_institution=serializer.validated_data.get('current_institution', ''),
            field_of_study=serializer.validated_data.get('field_of_study', ''),
            learning_goals=serializer.validated_data.get('learning_goals', ''),
            skills_to_develop=serializer.validated_data.get('skills_to_develop', ''),
            prior_experience=serializer.validated_data.get('prior_experience', ''),
            preferred_learning_format=serializer.validated_data.get('preferred_learning_format', ''),
            time_commitment=serializer.validated_data.get('time_commitment', ''),
            motivation=serializer.validated_data['motivation'],
            availability=serializer.validated_data.get('availability', ''),
            cohort_batch=cohort_batch,
            status='pending',
            applied_at=timezone.now(),
        )

        return Response({
            "success": True,
            "message": "Application submitted successfully!",
            "application": EducationCohortApplicationSerializer(application).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export education cohort applications to CSV"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        queryset = self.filter_queryset(self.get_queryset())

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'ID', 'Name', 'Email', 'Phone', 'Education Interest',
            'Current Education Level', 'Target Education Level', 'Current Institution',
            'Field of Study', 'Learning Goals', 'Skills to Develop', 'Prior Experience',
            'Preferred Learning Format', 'Time Commitment', 'Motivation', 'Availability',
            'Status', 'Cohort Batch', 'Applied At', 'Reviewed At', 'Reviewer Notes'
        ])

        for app in queryset:
            writer.writerow([
                str(app.id), app.name, app.email, app.phone or '',
                app.education_interest, app.current_education_level or '',
                app.target_education_level or '', app.current_institution or '',
                app.field_of_study or '', app.learning_goals or '',
                app.skills_to_develop or '', app.prior_experience or '',
                app.preferred_learning_format or '', app.time_commitment or '',
                app.motivation, app.availability or '', app.status,
                app.cohort_batch or '', app.applied_at, app.reviewed_at or '',
                app.reviewer_notes or ''
            ])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="education_cohort_applications_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        return response

    @action(detail=False, methods=['get'], url_path='analytics')
    def analytics(self, request):
        """Get education cohort application analytics"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from django.db.models import Count

        queryset = EducationCohortApplication.objects.all()

        return Response({
            "total_applications": queryset.count(),
            "by_status": dict(queryset.values_list('status').annotate(count=Count('id'))),
            "by_cohort_batch": dict(queryset.values_list('cohort_batch').annotate(count=Count('id'))),
            "pending_count": queryset.filter(status='pending').count(),
            "approved_count": queryset.filter(status='approved').count(),
            "rejected_count": queryset.filter(status='rejected').count(),
        })

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        """Bulk approve education cohort applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Approved')

        if not application_ids:
            return Response({"error": "application_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = EducationCohortApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='approved',
            reviewed_at=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully approved {updated_count} applications",
            "updated_count": updated_count
        })

    @action(detail=False, methods=['post'], url_path='bulk-reject')
    def bulk_reject(self, request):
        """Bulk reject education cohort applications"""
        if self._db_is_sqlite():
            return Response({"detail": "Remote data unavailable in sqlite mode"}, status=503)

        from apps.users.permissions import IsAdmin
        if not IsAdmin().has_permission(request, self):
            return Response({"detail": "Admin permission required"}, status=403)

        application_ids = request.data.get('application_ids', [])
        reviewer_notes = request.data.get('reviewer_notes', 'Rejected')

        if not application_ids:
            return Response({"error": "application_ids is required"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = EducationCohortApplication.objects.filter(
            id__in=application_ids
        ).update(
            status='rejected',
            reviewed_at=timezone.now(),
            reviewer_notes=reviewer_notes
        )

        return Response({
            "detail": f"Successfully rejected {updated_count} applications",
            "updated_count": updated_count
        })
