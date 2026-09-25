from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import CreateView, UpdateView

from django import forms

from kitsunerobotics.models import BlogImage
from kitsunerobotics.uploads import (
    all_chunks_present,
    assemble_chunks,
    chunk_exists,
    clean_upload_filename,
    clean_upload_id,
    max_upload_bytes,
    save_chunk,
    upload_chunk_bytes,
)
from siteblog.models import Article


class ArticleWriteForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ["title", "slug", "status", "published_on", "article_body"]
        widgets = {
            "article_body": forms.Textarea(attrs={"rows": 18}),
            "title": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ArticleWriteView(StaffRequiredMixin):
    model = Article
    form_class = ArticleWriteForm
    template_name = "editor/article_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["max_upload_bytes"] = max_upload_bytes()
        context["upload_chunk_bytes"] = upload_chunk_bytes()
        return context

    def form_valid(self, form):
        if not form.instance.slug:
            form.instance.slug = slugify(form.instance.title)[:50]
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("article_detail", args=[self.object.slug])


class ArticleCreateView(ArticleWriteView, CreateView):
    pass


class ArticleUpdateView(ArticleWriteView, UpdateView):
    slug_field = "slug"
    slug_url_kwarg = "slug"


@require_http_methods(["GET", "POST"])
def upload_chunk(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=401)

    params = request.GET if request.method == "GET" else request.POST
    upload_id = clean_upload_id(params.get("resumableIdentifier"))
    filename = clean_upload_filename(params.get("resumableFilename"))
    try:
        chunk_number = int(params.get("resumableChunkNumber") or 0)
        total_chunks = int(params.get("resumableTotalChunks") or 0)
        total_size = int(params.get("resumableTotalSize") or 0)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid upload metadata."}, status=400)

    if not upload_id or not filename or chunk_number < 1 or total_chunks < 1:
        return JsonResponse({"error": "Invalid upload metadata."}, status=400)
    if total_size > max_upload_bytes():
        return JsonResponse({"error": "That file is too large."}, status=413)

    if request.method == "GET":
        if chunk_exists(request.user.pk, upload_id, chunk_number):
            return HttpResponse(status=200)
        return HttpResponse(status=204)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": "No chunk provided"}, status=400)
    if uploaded.size > upload_chunk_bytes() + (256 * 1024):
        return JsonResponse({"error": "Chunk too large."}, status=400)

    save_chunk(request.user.pk, upload_id, chunk_number, uploaded)

    if not all_chunks_present(request.user.pk, upload_id, total_chunks):
        return JsonResponse({"success": True, "complete": False})

    saved = assemble_chunks(request.user.pk, upload_id, total_chunks, filename)
    return JsonResponse(
        {
            "success": True,
            "complete": True,
            "url": saved.image.url,
            "markdown": saved.markdown_link,
            "filename": saved.filename,
        }
    )


@require_POST
def upload_file(request):
    if not request.user.is_staff:
        return JsonResponse({"error": "Authentication required"}, status=401)

    uploaded = request.FILES.get("file") or request.FILES.get("image")
    if not uploaded:
        return JsonResponse({"error": "No file provided"}, status=400)
    if uploaded.size > max_upload_bytes():
        return JsonResponse({"error": "That file is too large."}, status=413)

    safe_name = clean_upload_filename(uploaded.name)
    if not safe_name:
        return JsonResponse({"error": "That file type can't be uploaded."}, status=400)

    uploaded.name = safe_name
    saved = BlogImage.objects.create(
        image=uploaded, uploaded_by=request.user, filename=safe_name
    )
    return JsonResponse(
        {
            "success": True,
            "url": saved.image.url,
            "markdown": saved.markdown_link,
            "filename": saved.filename,
        }
    )
