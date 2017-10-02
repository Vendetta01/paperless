from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import DetailView, FormView, TemplateView
from django_filters.rest_framework import DjangoFilterBackend
from paperless.db import GnuPG
from paperless.mixins import SessionOrBasicAuthMixin
from paperless.views import StandardPagination
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import (
    GenericViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet
)

from .filters import CorrespondentFilterSet, DocumentFilterSet, TagFilterSet
from .forms import UploadForm
from .models import Correspondent, Document, Log, Tag
from .serialisers import (
    CorrespondentSerializer,
    DocumentSerializer,
    LogSerializer,
    TagSerializer
)


class IndexView(TemplateView):

    template_name = "documents/index.html"

    def get_context_data(self, **kwargs):
        print(kwargs)
        print(self.request.GET)
        print(self.request.POST)
        return TemplateView.get_context_data(self, **kwargs)


class FetchView(SessionOrBasicAuthMixin, DetailView):

    model = Document

    def render_to_response(self, context, **response_kwargs):
        """
        Override the default to return the unencrypted image/PDF as raw data.
        """

        content_types = {
            Document.TYPE_PDF: "application/pdf",
            Document.TYPE_PNG: "image/png",
            Document.TYPE_JPG: "image/jpeg",
            Document.TYPE_GIF: "image/gif",
            Document.TYPE_TIF: "image/tiff",
        }

        if self.kwargs["kind"] == "thumb":
            return HttpResponse(
                GnuPG.decrypted(self.object.thumbnail_file),
                content_type=content_types[Document.TYPE_PNG]
            )

        response = HttpResponse(
            GnuPG.decrypted(self.object.source_file),
            content_type=content_types[self.object.file_type]
        )
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(
            self.object.file_name)

        return response


class PushView(SessionOrBasicAuthMixin, FormView):
    """
    A crude REST-ish API for creating documents.
    """

    form_class = UploadForm

    def form_valid(self, form):
        form.save()
        return HttpResponse("1", status=202)

    def form_invalid(self, form):
        return HttpResponseBadRequest(str(form.errors))


class CorrespondentViewSet(ModelViewSet):
    model = Correspondent
    queryset = Correspondent.objects.all()
    serializer_class = CorrespondentSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = CorrespondentFilterSet
    ordering_fields = ("name", "slug")


class TagViewSet(ModelViewSet):
    model = Tag
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = TagFilterSet
    ordering_fields = ("name", "slug")


class DocumentViewSet(RetrieveModelMixin,
                      UpdateModelMixin,
                      DestroyModelMixin,
                      ListModelMixin,
                      GenericViewSet):
    model = Document
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = DocumentFilterSet
    search_fields = ("title", "correspondent__name", "content")
    ordering_fields = (
        "id", "title", "correspondent__name", "created", "modified")
    
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(Document, self).get_context_data(**kwargs)
        # Add next free file number of current folder
        cur_folder = Document.objects.get(pk=self.pk).foldernumber
        context['next_free_filenum'] = Documents.objects.filter(foldernumber=cur_folder).latest('filenumber').filenumber+1
        print("DocumentViewSet: context: {}".format(context))
        return context


class LogViewSet(ReadOnlyModelViewSet):
    model = Log
    queryset = Log.objects.all().by_group()
    serializer_class = LogSerializer
    pagination_class = StandardPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("time",)
