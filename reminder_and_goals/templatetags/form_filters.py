from django import template

register = template.Library()

def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

register.filter("add_class", add_class)