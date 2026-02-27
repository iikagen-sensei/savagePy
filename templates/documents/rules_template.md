{% for rule in rules %}
# {{ rule.name }}{% if rule.name_original %} ({{ rule.name_original }}){% endif %}

{% if rule.description %}*{{ rule.description }}*

{% endif %}
{{ rule.content or '' }}

{% if rule.source == 'Oficial' %}{% set ref = rule.reference_book %}*{{ ref.title if ref and ref.title else 'Oficial' }}{% if rule.page_no %} p.{{ rule.page_no }}{% endif %}*{% elif rule.source == 'Terceros' %}*Terceros*{% else %}*Propio*{% endif %}

---
{% endfor %}
