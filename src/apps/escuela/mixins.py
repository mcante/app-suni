from django.shortcuts import redirect
from django.views.generic.base import ContextMixin
from apps.escuela.forms import ContactoTelefonoFormSet, ContactoMailFormSet


class ContactoContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(ContactoContextMixin, self).get_context_data(**kwargs)
        context['named_formsets'] = self.get_named_formsets()
        return context

    def get_named_formsets(self):
        return {
            'telefono': ContactoTelefonoFormSet(
                self.request.POST or None,
                prefix='telefono',
                instance=self.object),
            'mail': ContactoMailFormSet(
                self.request.POST or None,
                prefix='mail',
                instance=self.object),
        }

    def form_valid(self, form):
        named_formsets = self.get_named_formsets()
        if not all((x.is_valid() for x in named_formsets.values())):
            return self.render_to_response(self.get_context_data(form=form))
        else:
            self.object = form.save()

        for name, formset in named_formsets.items():
            formset.save()

        return redirect(self.get_success_url())

    def formset_telefono_valid(self, formset):
        telefonos = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()

        for telefono in telefonos:
            telefono.contacto = self.object
            telefono.save()

    def formset_mail_valid(self, formset):
        mails = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for mail in mails:
            mail.contacto = self.object
            mail.save()
