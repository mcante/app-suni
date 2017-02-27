from django.core.urlresolvers import reverse_lazy
from menu import Menu
from apps.main.menus import ViewMenuItem

# Administración
tpe_children = (
    ViewMenuItem(
        "Garantías",
        reverse_lazy("cooperante_list"),
        weight=10,
        icon="fa-gavel"),)

Menu.add_item(
    "user",
    ViewMenuItem(
        "Equipamiento",
        reverse_lazy('list_c'),
        weight=10,
        icon="fa-desktop",
        group="tpe",
        children=tpe_children))