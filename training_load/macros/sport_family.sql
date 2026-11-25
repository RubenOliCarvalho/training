{# Groups intervals.icu activity/event types so a planned "Run" matches a
   recorded "TrailRun", and "Ride" matches "VirtualRide". #}
{% macro sport_family(type_col) %}
    case
        when {{ type_col }} in ('Run', 'TrailRun', 'VirtualRun') then 'Run'
        when {{ type_col }} in ('Ride', 'VirtualRide', 'GravelRide', 'MountainBikeRide', 'EBikeRide') then 'Ride'
        else {{ type_col }}
    end
{% endmacro %}
