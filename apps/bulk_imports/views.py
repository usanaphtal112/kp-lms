from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView, ListView

from .forms import BulkImportUploadForm
from .mixins import BulkImportManagerRequiredMixin
from .models import ImportBatch
from .services import commit_import_batch, validate_import_file


class ImportBatchListView(BulkImportManagerRequiredMixin, ListView):
    model = ImportBatch
    template_name = "bulk_imports/batch_list.html"
    context_object_name = "batches"
    paginate_by = 20


class ImportUploadView(BulkImportManagerRequiredMixin, FormView):
    template_name = "bulk_imports/upload.html"
    form_class = BulkImportUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        try:
            batch = validate_import_file(
                importer_type=form.cleaned_data["importer_type"],
                uploaded_file=form.cleaned_data["file"],
                uploaded_by=self.request.user,
            )
        except Exception as exc:
            messages.error(self.request, str(exc))
            return self.form_invalid(form)

        messages.success(
            self.request,
            "File validated. Review the rows before committing the import.",
        )

        return redirect("bulk_imports:batch_detail", pk=batch.pk)


class ImportBatchDetailView(BulkImportManagerRequiredMixin, DetailView):
    model = ImportBatch
    template_name = "bulk_imports/batch_detail.html"
    context_object_name = "batch"

    def get_queryset(self):
        return ImportBatch.objects.prefetch_related("rows")


class ImportBatchCommitView(BulkImportManagerRequiredMixin, View):
    def post(self, request, pk):
        batch = ImportBatch.objects.get(pk=pk)

        if batch.invalid_rows:
            messages.error(
                request,
                "This import has invalid rows. Fix the file and upload again.",
            )
            return redirect("bulk_imports:batch_detail", pk=batch.pk)

        commit_import_batch(batch=batch, actor=request.user)

        messages.success(request, "Import committed successfully.")

        return redirect("bulk_imports:batch_detail", pk=batch.pk)