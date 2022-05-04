#!/usr/bin/env python3
"""
============================
__title__  = "E9 Reference-Template push script"
__author__ = "Charles F. Port"
__copyright__ = "Copyright 04APR22"
__credits__ = ["Charles F. Port"]
__license__ = "GPL"
__version__ = "0.0.2"
__modified__ = 12APR22
__maintainer__ = "TBD"
__email__ = "charles.port@calix.com"
__status__ = "Test"

============================
TERMS AND CONDITIONS FOR USE
============================

1. This software is provided by the author "as is" and any express or implied
warranties, including, but not limited to, the implied warranties of
marketability and fitness for a particular purpose are disclaimed. In no
event shall the author be liable for any direct, indirect, incidental,
special, exemplary, or consequential damages (including, but not limited to,
procurement of substitute goods or services; loss of use, data, or profits; or
business interruption) however caused and on any theory of liability, whether
in contract, strict liability, or tort (including negligence or otherwise)
arising in any way out of the use of this software, even if advised of the
possibility of such damage.

2. No Support. Neither the author (nor Calix, Inc.) will provide support.

3. USE AT YOUR OWN RISK

============================
END OF TERMS AND CONDITIONS
============================

Changes:
========

12APR22:
--------
1. General cleanup after lint run.
2. Changed function order.
./push_calix_ref_config.py
"""

###############################################################################
# IMPORT PYTHON3 LIBS
###############################################################################
import sys
from getpass import getpass as gp
from pprint import pprint as pp
import logging
import jinja2
import yaml
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

#============================
# REF CONFIGURATION VARIABLES
#============================
######################################################################
# !!# basic settings [1]
######################################################################
basic_settings_yaml = """
ipv4_static_hosts:
  host_1:
    - { ipv4_addr: "172.23.43.251", name_fqdn: "petnis01.calix.local" }
  host_2:
    - { ipv4_addr: "10.200.0.204" , name_fqdn: "sjclnx-st01.calix.local" }
  host_3:
    - { ipv4_addr: "10.136.10.34" , name_fqdn: "slc-scratch.caal.dev" }
ipv4_ntp_servers:
  ntp1:
    - { ntp_srv_no: "1", ipv4_addr: ,
        ntp_fqdn: "petnis01.calix.local" }
  ntp2:
    - { ntp_srv_no: "2", ipv4_addr: ,
        ntp_fqdn: "sjclnx-st01.calix.local", source_int: "system-craft" }
aaa:
    # tacacs-if-up-else-local Authenticate via tacacs [only] if up, else local
    # tacacs-then-local       Authenticate using tacacs then local database
    auth_order: 'tacacs-then-local'
    source_interface: 'system-craft'
    tac_srv_ipaddr: '10.200.0.212'
    tacacs_secret: '$1001$U2FsdGVkX1+jB4mHhWV3OLaDrEFbkm3smdVAG/kTC3Z1OQ=='
    # FIXED AAA ROLES:
    # admin  calixsupport  networkadmin  oper  ro
    user:
        - ['calixsupport','$1$qdmQFTMT$aaOZdqIzWwQsfSU5pc4XT0','calixsupport']
        - ['monitor','$1$bo6RaxHE$prYA2waVd/o4atvb1H8l8/','oper']
        - ['networkadmin','$1$henWME92$LqNxDU3.wWG19Fz.AlL5H0','networkadmin']
        - ['support','$1$s4LUL/4m$aQjOzqPRi/CUHpaYTGLGz/','oper']
        - ['sysadmin','$1$.fwnoBuy$fmIOhTEfd3RGyOSiwaQA40','admin']
ont_upg_srv:
    ous:
    - { source_int: "system-craft", ipaddr: "10.136.10.34",
        username: "cafetest", passwd: '$1001$U2FsdGVkX1/K59XU+GRgqOOPgVk5Jfp0',
        port: 21 }
"""
######################################################################
# !!# basic settings [1]
######################################################################
basic_settings_jinja = """
{#
 ########################
 # BASIC SETTINGS
 ########################
-#}
{% for sh in ipv4_static_hosts -%}
{% set attb = ipv4_static_hosts[sh] -%}
{% for i in attb -%}
ip host {{ i.name_fqdn }} {{ i.ipv4_addr }}
{% endfor -%}
{% endfor -%}
{% for ts in ipv4_ntp_servers -%}
{% set list_ts = ipv4_ntp_servers[ts] -%}
{% for i in list_ts -%}
{% if (i.ntp_srv_no is defined) and (i.ntp_srv_no is not none) -%}
ntp server {{ i.ntp_srv_no }} {{ i.ntp_fqdn }}
{% endif -%}
{% if (i.source_int is defined) and (i.source_int is not none) -%}
ntp source-interface {{ i.source_int }}
{% endif -%}
{% endfor -%}
{% endfor -%}
aaa authentication-order {{ aaa.auth_order }}
aaa tacacs source-interface {{ aaa.source_interface }}
aaa tacacs server {{ aaa.tac_srv_ipaddr }} secret  {{ aaa.tacacs_secret }}
{% for login, passwd, role  in aaa.user -%}
aaa user {{ login }} password {{ passwd }} role {{ role }}
{% endfor -%}
"""
######################################################################
# !!# ipv4 prefix list [2]
######################################################################
prefix_list_yaml = """
ip_prefix_list: 
  netconf-access:
    - { seq_no: 10,  seq_match: "172.23.34.0/24" }
  copp-acl-e9host:
    - { seq_no: 10,   seq_match: "15.10.10.0/24" }
    - { seq_no: 20,   seq_match: "15.10.11.0/24" }
    - { seq_no: 30,   seq_match: "15.10.12.0/24" }
    - { seq_no: 40,   seq_match: "15.10.13.0/24" }
    - { seq_no: 50,   seq_match: "15.10.14.0/24" }
    - { seq_no: 60,   seq_match: "15.10.15.0/24" }
    - { seq_no: 70,   seq_match: "15.10.16.0/24" }
    - { seq_no: 80,   seq_match: "15.10.17.0/24" }
    - { seq_no: 90,   seq_match: "15.10.18.0/24" }
    - { seq_no: 100,  seq_match: "15.10.19.0/24" }
    - { seq_no: 110,  seq_match: "15.10.20.0/24" }
    - { seq_no: 120,  seq_match: "15.10.21.0/24" }
    - { seq_no: 130,  seq_match: "15.10.22.0/24" }
    - { seq_no: 140,  seq_match: "15.10.23.0/24" }
    - { seq_no: 150,  seq_match: "15.10.24.0/24" }
    - { seq_no: 160,  seq_match: "15.10.25.0/24" }
    - { seq_no: 170,  seq_match: "15.10.26.0/24" }
    - { seq_no: 180,  seq_match: "15.10.27.0/24" }
    - { seq_no: 190,  seq_match: "15.10.28.0/24" }
    - { seq_no: 200,  seq_match: "15.10.29.0/24" }
    - { seq_no: 210,  seq_match: "15.10.30.0/24" }
    - { seq_no: 220,  seq_match: "15.10.31.0/24" }
    - { seq_no: 230,  seq_match: "15.10.32.0/24" }
    - { seq_no: 240,  seq_match: "15.10.33.0/24" }
    - { seq_no: 250,  seq_match: "15.10.34.0/24" }
    - { seq_no: 260,  seq_match: "15.10.35.0/24" }
    - { seq_no: 270,  seq_match: "15.10.36.0/24" }
    - { seq_no: 280,  seq_match: "15.10.37.0/24" }
    - { seq_no: 290,  seq_match: "140.1.1.1/32" }
    - { seq_no: 300,  seq_match: "15.0.0.1/32" }
    - { seq_no: 310,  seq_match: "15.0.0.0/24" }
  local_interfaces:
    - { seq_no: 10,   seq_match: "10.28.123.129/32" }
    - { seq_no: 20,   seq_match: "15.0.0.1/32" }
    - { seq_no: 30,   seq_match: "10.28.120.129/32" }
    - { seq_no: 50,   seq_match: "107.150.15.1/32" }
    - { seq_no: 55,   seq_match: "107.150.16.1/32" }
    - { seq_no: 60,   seq_match: "107.150.128.1/32" }
    - { seq_no: 65,   seq_match: "107.150.144.1/32" }
    - { seq_no: 70,   seq_match: "107.150.64.1/32" }
    - { seq_no: 75,   seq_match: "107.150.0.1/32" }
    - { seq_no: 80,   seq_match: "107.150.4.1/32" }
    - { seq_no: 85,   seq_match: "10.29.84.1/32" }
    - { seq_no: 90,   seq_match: "10.29.86.1/32" }
    - { seq_no: 95,   seq_match: "10.29.85.1/32" }
    - { seq_no: 100,  seq_match: "192.168.7.1/32" }
    - { seq_no: 105,  seq_match: "10.28.120.129/32" }
  ssh_config_servers_oob:
    - { seq_no: 10,  seq_match: "10.201.32.0/22" }
  vod_server:
    - { seq_no: 10,  seq_match: "10.20.0.0/16" }
  voip_subscriber_network:
    - { seq_no: 10,  seq_match: "10.28.123.128/25" }
  in-data:
    - { seq_no: 5,  seq_match: "0.0.0.0/0" }
  in-video:
    - { seq_no: 5,  seq_match: "0.0.0.0/0" }
  in-voice:
    - { seq_no: 5,  seq_match: "0.0.0.0/0" }
  out-data:
    - { seq_no: 5,  seq_match: "107.150.16.0/20 ge 20 le 20" }
    - { seq_no: 10, seq_match: "107.150.128.0/20 ge 20 le 20" }
  out-video:
    - { seq_no: 5,  seq_match: "49.49.49.0/24" }
  out-voice:
    - { seq_no: 5,  seq_match: "59.59.59.0/24" }
    - { seq_no: 10,  seq_match: "10.128.128.0/29 ge 29 le 29" }
"""
######################################################################
# !!# ipv4 prefix list [2]
######################################################################
prefix_list_jinja = """
{#
 ##################
 # IPV4 PREFIX LIST
 ##################
-#}
{% for pl in ip_prefix_list -%}
{% set attb =  ip_prefix_list[pl] -%}
ip prefix-list {{ pl }}
 {% for i in attb -%}
 seq {{ i.seq_no }} {{ i.seq_match }}
 {% endfor -%}
 {% if loop.cycle -%}
!
{%endif -%}
{% endfor -%}
"""
######################################################################
# !!# ipv4 access list [3]
######################################################################
access_list_yaml = """
acl_list:
  craft_interface_control_ipv4:
    - { ipv4: "yes", description: }
    - { rule_no: 30, rule_desc: "dst-traceroute", rule_match_proto: "udp",
        rule_match_specs: "destination-port-range 33434-33523", rule_action: "permit",
        rule_cpu_cosq: "", rule_count: "count" }
    - { rule_no: 60, rule_desc: '"allow-src-sp_ssh 01"', rule_match_src_prefix: "ssh_config_servers_oob",
        rule_match_specs: "destination-port-range ssh", rule_match_proto: "tcp",
        rule_action: "permit", rule_cpu_cosq: " ", rule_count: "count" }
    - { rule_no: 70, rule_desc: "allow-src-sp_netconf", rule_match_src_prefix: "netconf-access",
        rule_match_specs: "destination-port-range 830", rule_match_proto: "tcp",
        rule_action: "permit", rule_cpu_cosq: " ", rule_count: "count" }
    - { rule_no: 255, rule_desc: "deny-all", rule_match_any: "any", rule_action: "deny", rule_count: "count" }
  control_plane_access_list_ipv4:
    - { ipv4: "yes", description: "control plane filter ipv4" }
    - { rule_no: 10, rule_desc: "limit-10m-dst-dhcp", rule_match_proto: "UDP",
        rule_match_specs: "source-port-range 68 destination-port-range 67-68",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 28",
        rule_count: "count" }
    - { rule_no: 22, rule_match_misc: "source-ipv4-network 107.150.0.2/32 protocol TCP destination-port-range 179",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 42", rule_count: "count" }
    - { rule_no: 23, rule_match_misc: "source-ipv4-network 107.150.0.1/32 protocol TCP source-port-range 179",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 43", rule_count: "count" }
    - { rule_no: 29, rule_desc: "limit-srcdst-icmp-sp", rule_match_proto: "ICMP",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 2", rule_count: "count" }
    - { rule_no: 30, rule_desc: "limit-1m-dst-traceroute", rule_match_proto: "UDP",
        rule_match_specs: "destination-port-range 33434-33523", rule_action: "permit",
        rule_cpu_cosq: "cpu-cosq 3", rule_count: "count" }
    - { rule_no: 38, rule_desc: "access_to_voice_server", rule_match_dest_prefix: "out-voice",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 44", rule_count: "count" }
    - { rule_no: 40, rule_desc: "access_to_VOD_server", rule_match_dest_prefix: "vod_server",
        rule_action: "permit", rule_cpu_cosq: " ", rule_count: "count" }
    - { rule_no: 52, rule_match_misc: "source-port-range BOOTPC",
        rule_action: "permit", rule_cpu_cosq: "cpu-cosq 6", rule_count: "count" }
    - { rule_no: 61, rule_desc: '"E9 access"', rule_match_dest_prefix: "copp-acl-e9host",
        rule_action: "permit", rule_cpu_cosq: " ", rule_count: "count" }
    - { rule_no: 255, rule_desc: "deny-all", rule_match_any: "any", rule_action: "deny", rule_count: "count" }
"""
######################################################################
# !!# ipv4 access list [3]
######################################################################
access_list_jinja = """
{#
 ##################
 # ACL RULES
 ##################
-#}
{% for acl in acl_list -%}
{% set attrb0 = acl_list[acl] -%}
{% for i in attrb0 -%}
{%- if (i.ipv4 is defined) and i.ipv4 == "yes" -%}
access-list ipv4 {{ acl }}
 {% endif -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description "{{ i.description }}"
 {% endif -%}
 {% if (i.rule_desc is defined) and (i.rule_desc is not none) -%}
 rule {{ i.rule_no }} description {{ i.rule_desc }}
 {% endif -%}
 {% if (i.rule_match_proto is defined) and (i.rule_match_proto is not none) -%}
 rule {{ i.rule_no }} match protocol {{ i.rule_match_proto }} {{ i.rule_match_specs }}
 {% endif -%}
 {% if (i.rule_match_src_prefix is defined) and (i.rule_match_src_prefix is not none) -%}
 rule {{ i.rule_no }} match source-ipv4-prefix-list {{ i.rule_match_src_prefix }} {{ i.rule_match_specs }}
 {% endif -%}
 {% if (i.rule_match_dest_prefix is defined) and (i.rule_match_dest_prefix is not none) -%}
 rule {{ i.rule_no }} match destination-ipv4-prefix-list {{ i.rule_match_dest_prefix }} {{ i.rule_match_specs }}
 {% endif -%}
 {% if (i.rule_match_any is defined) and (i.rule_match_any is not none) -%}
 rule {{ i.rule_no }} match {{ i.rule_match_any }}
 {% endif -%}
 {% if (i.rule_match_misc is defined) and (i.rule_match_misc is not none) -%}
 rule {{ i.rule_no }} match {{ i.rule_match_misc }}
 {% endif -%}
 {% if (i.rule_action is defined) and (i.rule_action is not none) -%}
 rule {{ i.rule_no }} action {{ i.rule_action }} {{ i.rule_cpu_cosq }} {{ i.rule_count }}
 {% endif -%}
{% if (i.ipv6 is defined) and i.ipv6 == "yes" %}
access-list ipv6 {{ acl }}
{% endif -%}
 {% if i.description_v6 is defined and not none %}
 description "{{ i.description_v6 }}"
 {% endif -%}
 {% if (i.rule_desc_v6 is defined) and (i.rule_desc_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} description {{ i.rule_desc_v6 }}
 {% endif -%}
 {% if (i.rule_match_proto_v6 is defined) and (i.rule_match_proto_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} match {{ i.rule_match_proto_v6 }} {{ i.rule_match_specs_v6 }}
 {% endif -%}
 {% if (i.rule_match_src_prefix_v6 is defined) and (i.rule_match_src_prefix_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} match source-ipv6-prefix-list {{ i.rule_match_src_prefix_v6 }} {{ i.rule_match_specs_v6 }}
 {% endif -%}
 {% if (i.rule_match_dest_prefix_v6 is defined) and (i.rule_match_dest_prefix_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} match destination-ipv6-prefix-list {{ i.rule_match_dest_prefix_v6 }} {{ i.rule_match_specs_v6 }}
 {% endif -%}
 {% if (i.rule_match_any_v6 is defined) and (i.rule_match_any_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} match {{ i.rule_match_any_v6 }}
 {% endif -%}
 {% if (i.rule_action_v6 is defined) and (i.rule_action_v6 is not none) -%}
 rule {{ i.rule_no_v6 }} action {{ i.rule_action_v6 }} {{ i.rule_cpu_cosq_v6 }} {{ i.rule_count_v6 }}
 {% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# cos cosq profile [4]
######################################################################
cos_cosq_profiles_yaml = """
cos_profile:
  cosq-control_plane:
    - { cosq_entry: 1, max_bandwidth: 1000, }
    - { cosq_entry: 2, max_bandwidth: 1000, }
    - { cosq_entry: 3, max_bandwidth: 1000, }
    - { cosq_entry: 4, max_bandwidth: 500,  }
    - { cosq_entry: 5, max_bandwidth: 500,  }
    - { cosq_entry: 6, max_bandwidth: 500,  }
    - { cosq_entry: 7, max_bandwidth: 1000, }
    - { cosq_entry: 10, max_bandwidth: 1000, }
    - { cosq_entry: 11, max_bandwidth: 64, }
    - { cosq_entry: 12, max_bandwidth: 64, queue_depth: 128000, }
    - { cosq_entry: 13, }
    - { cosq_entry: 14, }
    - { cosq_entry: 15, }
    - { cosq_entry: 16, }
    - { cosq_entry: 25, max_bandwidth: 1000, }
    - { cosq_entry: 26, max_bandwidth: 10000, }
    - { cosq_entry: 27, }
    - { cosq_entry: 28, max_bandwidth: 10000, }
    - { cosq_entry: 30, }
    - { cosq_entry: 31, max_bandwidth: 1000, }
    - { cosq_entry: 32, max_bandwidth: 500, }
    - { cosq_entry: 33, }
    - { cosq_entry: 34, }
    - { cosq_entry: 35, max_bandwidth: 500, }
    - { cosq_entry: 36, max_bandwidth: 500, }
    - { cosq_entry: 37, max_bandwidth: 128, }
    - { cosq_entry: 40, }
    - { cosq_entry: 41, max_bandwidth: 1000, }
    - { cosq_entry: 42, max_bandwidth: 10000, }
    - { cosq_entry: 43, max_bandwidth: 10000, }
    - { cosq_entry: 44, max_bandwidth: 1000, }
  pon-cos:
    - { cosq_group_scheduling_type: "3SP-3WRR", cosq_entry: 1, }
"""
######################################################################
# !!# cos cosq profile [4]
######################################################################
cos_cosq_profiles_jinja = """
{#
 ##################
 # COS COSQ PROFILE
 ##################
-#}
{% for cos in cos_profile -%}
cos cosq-profile {{ cos }}
 {% set attr0 = cos_profile[cos] -%}
 {% for i in attr0 -%}
 {% if (i.cosq_group_scheduling_type is defined) and (i.cosq_group_scheduling_type is not none) -%}
 cosq-group-scheduling-type {{ i.cosq_group_scheduling_type }}
 {% endif -%}
 {% if (i.cosq_entry is defined) and (i.cosq_entry is not none) -%}
 cosq-entry {{ i.cosq_entry }}
  {% endif -%}
  {% if (i.max_bandwidth is defined) and (i.max_bandwidth is not none) -%}
  bandwidth maximum {{ i.max_bandwidth }}
  {% endif -%}
  {% if (i.queue_depth is defined) and (i.queue_depth is not none) -%}
  queue-depth    {{ i.queue_depth }}
  {% endif -%}
  {% if (i.discard_policy is defined) and (i.discard_policy is not none) -%}
  discard-policy {{ i.discard_policy }}
  {% endif -%}
 {% if loop.cycle -%}
 !
 {% endif -%}
 {% endfor -%}
{%- if loop.cycle -%}
!
{% endif -%}
{% endfor -%}
"""
######################################################################
# !!# oob mgmt [5]
######################################################################
out_of_band_mgmt_yaml = """
craft_info:
  1/1/2:
    - { desc: "craft interface 1/1/2", cosq: , dhcp_state: "disable", ipv4_acl: "craft_interface_control_ipv4", vrf_name: ,
        ip_addr_v4_w_mask: "10.137.13.195/21", ip_addr_v6_w_mask: , shutdown_state: "no shutdown" }
  1/2/2:
    - { desc: "craft interface 1/2/2", cosq: , dhcp_state: "disable", ipv4_acl: "craft_interface_control_ipv4", vrf_name: ,
        ip_addr_v4_w_mask: "10.137.13.196/21", ip_addr_v6_w_mask: , shutdown_state: "no shutdown" }
sys_craft:
  1:
  - { desc: "System Craft for Triple_play",  dhcp_server_state: "disable", dhcp_fwd_vrf: , dhcp_fwd_vrf_ipv4: ,
      ip_addr_v4_w_mask: "10.137.13.194/32", dhcp_fwd_vrf_ipv6: , sys_int_state: "no shutdown" }
"""
######################################################################
# !!# oob mgmt [5]
######################################################################
out_of_band_mgmt_jinja = """
{#
 ########################
 # SYSTEM CRAFT INTERFACE
 ########################
-#}
{% for sys_int in sys_craft -%}
{% set attrb0 = sys_craft[sys_int] -%}
interface system-craft {{ sys_int }}
 {% for i in attrb0 -%}
 {% if (i.desc is defined) and (i.desc is not none) -%}
 description "{{ i.desc }}"
 {% endif -%}
 {% if (i.dhcp_server_state is defined) and (i.dhcp_server_state is not none) -%}
 ip dhcp server {{ i.dhcp_server_state }}
 {% endif -%}
 {% if (i.dhcp_fwd_vrf is defined) and (i.dhcp_fwd_vrf is not none) -%}
 ip vrf forwarding {{ i.dhcp_fwd_vrf }}
  {% if (i.dhcp_fwd_vrf_ipv4 is defined) and (i.dhcp_fwd_vrf_ipv4 is not none) -%}
  ip address {{ i.dhcp_fwd_vrf_ipv4 }}
  {% endif -%}
  {% if (i.dhcp_fwd_vrf_ipv6 is defined) and (i.dhcp_fwd_vrf_ipv6 is not none) -%}
  ipv6 address {{ i.dhcp_fwd_vrf_ipv6 }}
  {% endif -%}
 !
 {% else -%}
 ip address {{ i.ip_addr_v4_w_mask }}
 {% endif -%}
{% if (i.sys_int_state is defined) and (i.sys_int_state is not none) -%}
 {{ i.sys_int_state }}
 {% endif -%}
!
{% endfor -%}
{% endfor -%}
{#
 #################
 # CRAFT INTERFACE
 #################
-#}
{% for craft in craft_info -%}
interface craft {{ craft }}
 {% set attrb1 = craft_info[craft] -%}
 {% for i in attrb1 -%}
 {% if (i.desc is defined) and (i.desc is not none) -%}
 description "{{ i.desc }}"
 {% endif -%}
 {% if (i.ipv4_acl is defined) and (i.ipv4_acl is not none) -%}
 access-group ipv4-acl {{ i.ipv4_acl }}
 {% endif -%}
 {% if i.cosq is not none -%}
 cosq      {{ i.cosq }}
 {% endif -%}
 ip dhcp server {{ i.dhcp_state }}
 {% if (i.vrf_name is defined) and (i.vrf_name is not none) -%}
  ip vrf forwarding {{ i.vrf_name|upper }}
  ip address {{ i.ip_addr_v4_w_mask }}
  ipv6 address {{ i.ip_addr_v6_w_mask }}
 {% else -%}
 ip address {{ i.ip_addr_v4_w_mask }}
 {% endif -%}
 !
 {{ i.shutdown_state }}
!
{% endfor -%}
{% endfor -%}
"""
######################################################################
# !!# cntrl plane [6]
######################################################################
cntrl_plane_yaml = """
cntrl_plane:
  - type: "cosq"
    filter_name: "cosq-control_plane"
  - type: "access-group"
    proto_acl: "ipv4-acl"
    filter_name: "control_plane_access_list_ipv4"
# - type: "access-group"
#   proto_acl: "ipv6-acl"
#   filter_name: "control_plane_access_list_ipv6"
"""
######################################################################
# !!# cntrl plane [6]
######################################################################
cntrl_plane_jinja = """
{#
 #################
 # CONTROL-PLANE
 #################
-#}
{% for cntrl_elem in cntrl_plane -%}
{% if (cntrl_elem.proto_acl is defined) and (cntrl_elem.proto_acl is not none) -%}
control-plane {{ cntrl_elem.type }} {{ cntrl_elem.proto_acl }} {{ cntrl_elem.filter_name }}
{% else -%}
control-plane {{ cntrl_elem.type }} {{ cntrl_elem.filter_name }}
{% endif -%}
{% endfor -%}
!
"""
######################################################################
# !!# redistribution [7]
######################################################################
redist_cfg_yaml = """
redist:
  redist1:
    - { name: "out-data", name_no: 5, match_prefix: "out-data" }
  redist2:
    - { name: "out-video", name_no: 5, match_prefix: "out-video" }
  redist3:
    - { name: "out-voice", name_no: 5, match_prefix: "out-voice" }
"""
######################################################################
# !!# redistribution [7]
######################################################################
redist_cfg_jinja = """
{#
 #################
 # REDISTRIBUTION
 #################
-#}
{% for rm in redist-%}
{% set attr0 = redist[rm] -%}
{% for i in attr0 -%}
{% if (i.name is defined) and (i.name is not none) -%}
redist-map {{ i.name }} {{ i.name_no }}
 {% if (i.match_prefix is defined) and (i.match_prefix is not none) -%}
 match prefix-list {{ i.match_prefix }}
 {% endif -%}
 {% if (i.match_prefix_v4 is defined) and (i.match_prefix_v4 is not none) -%}
 match prefix-list ipv4 {{ i.match_prefix_v4 }}
 {% endif -%}
 {% if (i.match_prefix_v6 is defined) and (i.match_prefix_v6 is not none) -%}
 match prefix-list ipv6 {{ i.match_prefix_v6 }}
 {% endif -%}
 {% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# ip vrf configuration [8]
######################################################################
vrf_cfg_yaml = """
ip_vrf:
  unicastvideo:
  - { description: "Unicast Video VRF", ip_route_det: "0.0.0.0/0 next-hop NULL0 distance 255", router_bgp: "65501", redist_map: "out-video", rtr_id: "107.150.15.100",
     graceful_restart_enable: "enable", graceful_restart_stalepath_time: 360, graceful_restart_path_selection_defer_time: , maximum_paths_ebgp: , bgp_policy_map: "in-video",
     bgp_rule: 5, bgp_address_family: "ipv4-unicast", bgp_address_family_prefix_list: "in-video" }
  - { bgp_neighbor_ipaddr: "107.150.4.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: ,
      bgp_neighbor_update_source: , bgp_neighbor_bfd: , bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-video",
      bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group: }
  - { bgp_neighbor_ipaddr: "107.150.4.0", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: ,
      bgp_neighbor_update_source: , bgp_neighbor_bfd: , bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-video",
      bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group: }
 # - { bgp_neighbor_ipaddr: "105.40.11.3", bgp_neighbor_remote_as: 101, bgp_neighbor_weight: 100, soft_reconfiguration: "soft-reconfiguration", bgp_neighbor_update_source: "105.40.11.2", bgp_neighbor_bfd: "BFDP-WAN-01",
 #     bgp_neighbor_addr_family_details_ipv4_1: "ipv4 multicast", bgp_neighbor_addr_family_state_ipv4_1: "disable",
 #     bgp_neighbor_addr_family_details_ipv4_2: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_2: "enable",
 #     bgp_neighbor_addr_family_details_ipv4_3: "ipv4 vpnv4", bgp_neighbor_addr_family_state_ipv4_3: "disable",
 #     bgp_neighbor_addr_family_details_ipv6_1: "ipv6 multicast", bgp_neighbor_addr_family_state_ipv6_1: "disable",
 #     bgp_neighbor_addr_family_details_ipv6_2: "ipv6 unicast", bgp_neighbor_addr_family_state_ipv6_2: "disable",
 #     bgp_neighbor_addr_family_details_ipv6_3: "ipv6 vpnv4", bgp_neighbor_addr_family_state_ipv6_3: "disable",
 #     bgp_neighbor_addr_family_details_misc: "l2vpn multicast",
 #     bgp_neighbor_passwd: "test", bgp_neighbor_policy_map_in: "VOIP-IN", bgp_neighbor_policy_map_out: "VOIP-OUT",bgp_neighbor_gnmi_group: "pm-bgp-stat"  }
  voice:
  - { description: "Voice VRF", ip_route_det: "0.0.0.0/0 next-hop NULL0 distance 255" , router_bgp: "65501", redist_map: "out-voice", rtr_id: "107.150.15.10",
      graceful_restart_enable: "enable", graceful_restart_stalepath_time: 360, graceful_restart_path_selection_defer_time:  ,maximum_paths_ebgp:  ,bgp_policy_map: "in-voice",
      bgp_rule: 5, bgp_address_family: "ipv4-unicast", bgp_address_family_prefix_list: "in-voice" }
  - { bgp_rule: 10, bgp_address_family: "ipv4-unicast", bgp_address_family_action: "deny" }
  - { bgp_neighbor_ipaddr: "107.150.4.0", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: ,
      bgp_neighbor_update_source: , bgp_neighbor_bfd: , bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-voice" }
  - { bgp_neighbor_ipaddr: "107.150.4.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: ,
      bgp_neighbor_update_source: , bgp_neighbor_bfd: , bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-voice" }

"""
######################################################################
# !!# ip vrf configuration [8]
######################################################################
vrf_cfg_jinja = """
{#
 #################
 # IP VRF w/BGP
 #################
-#}
{% for vrf in ip_vrf -%}
{% set attrb0 = ip_vrf[vrf] -%}
ip vrf {{ vrf }}
 {% for i in attrb0 -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description "{{ i.description }}"
 {% endif -%}
 {% if (i.ip_route_det is defined) and (i.ip_route_det is not none) -%}
 ip route {{ i.ip_route_det }}
 {% endif -%}
 {% if (i.ipv6_route_det is defined) and (i.ipv6_route_det is not none) -%}
 ipv6 route {{ i.ipv6_route_det }}
 {% endif -%}
 {% if (i.router_bgp is defined) and (i.router_bgp is not none) -%}
 router bgp {{ i.router_bgp }}
  {% endif -%}
  {% if (i.redist_map is defined) and (i.redist_map is not none) -%}
  redistribute connected redist-map {{ i.redist_map }}
  {% endif -%}
  {% if (i.rtr_id is defined) and (i.rtr_id is not none) -%}
  router-id {{ i.rtr_id }}
  {% endif -%}
  {% if (i.graceful_restart_enable is defined) and (i.graceful_restart_enable is not none) -%}
  graceful-restart          {{ i.graceful_restart_enable }}
  {% endif -%}
  {% if (i.graceful_restart_stalepath_time is defined) and (i.graceful_restart_stalepath_time is not none) -%}
  graceful-restart stalepath-time {{ i.graceful_restart_stalepath_time }}
  {% endif -%}
  {% if (i.graceful_restart_path_selection_defer_time is defined) and (i.graceful_restart_path_selection_defer_time is not none) -%}
  graceful-restart path-selection-defer-time {{ i.graceful_restart_path_selection_defer_time }}
  {% endif -%}
  {% if (i.maximum_paths_ebgp is defined) and (i.maximum_paths_ebgp is not none) -%}
  maximum-paths ebgp {{ i.maximum_paths_ebgp }}
  {% endif -%}
  {% if (i.bgp_policy_map is defined) and (i.bgp_policy_map is not none) -%}
  bgp-policy-map {{ i.bgp_policy_map }}
   {% endif -%}
   {% if (i.bgp_rule is defined) and (i.bgp_rule is not none) -%}
   rule {{ i.bgp_rule }}
    {% endif -%}
    {% if (i.bgp_address_family is defined) and (i.bgp_address_family is not none) -%}
    address-family {{ i.bgp_address_family }}
    {% endif -%}
    {% if (i.bgp_address_family_prefix_list is defined) and (i.bgp_address_family_prefix_list is not none) -%}
     match prefix-list {{ i.bgp_address_family_prefix_list }}
    {% endif -%}
    {% if (i.bgp_address_family_community_list is defined) and (i.bgp_address_family_community_list is not none) -%}
     set community-list {{ i.bgp_address_family_community_list }}
    {% endif -%}
    {% if (i.bgp_address_family_action is defined) and (i.bgp_address_family_action is not none) -%}
     {{ i.bgp_address_family_action }}
    {% endif -%}
    !
   {% if i.bgp_rule == 10 -%}
   !
   {% endif -%}
  {% if (i.bgp_neighbor_ipaddr is defined) and (i.bgp_neighbor_ipaddr is not none) -%}
  neighbor {{ i.bgp_neighbor_ipaddr }}
   {% if (i.bgp_neighbor_remote_as is defined) and (i.bgp_neighbor_remote_as is not none) -%}
   remote-as            {{ i.bgp_neighbor_remote_as }}
   {% endif -%}
   {% if (i.bgp_neighbor_weight is defined) and (i.bgp_neighbor_weight is not none) -%}
   weight               {{ i.bgp_neighbor_weight }}
   {% endif -%}
   {% if (i.soft_reconfiguration is defined) and (i.soft_reconfiguration is not none) -%}
   {{ i.soft_reconfiguration }}
   {% endif -%}
   {% if (i.bgp_neighbor_update_source is defined) and (i.bgp_neighbor_update_source is not none) -%}
   update-source        {{ i.bgp_neighbor_update_source }}
   {% endif -%}
   {% if (i.bgp_neighbor_bfd is defined) and (i.bgp_neighbor_bfd is not none) -%}
   bfd                  {{ i.bgp_neighbor_bfd }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv4_1 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_1 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv4_1 }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_ipv4_1 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_1 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv4_1 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv4_2 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_2 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv4_2 }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_ipv4_2 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_2 is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_ipv4_2 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv4_3 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_3 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv4_3 }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_ipv4_3 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_3 is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_ipv4_3 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv6_1 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_1 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv6_1 }}
    {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv6_1 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_1 is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_ipv6_1 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv6_2 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_2 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv6_2 }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_ipv6_2 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_2 is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_ipv6_2 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_ipv6_3 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_3 is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_ipv6_3 }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_ipv6_3 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_3 is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_ipv6_3 }}
   !
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_details_misc is defined) and (i.bgp_neighbor_addr_family_details_misc is not none) -%}
   address-family {{ i.bgp_neighbor_addr_family_details_misc }}
   {% endif -%}
   {% if (i.bgp_neighbor_addr_family_state_misc is defined) and (i.bgp_neighbor_addr_family_state_misc is not none) -%}
     {{ i.bgp_neighbor_addr_family_state_misc }}
   !
   {% endif -%}
   {% endif -%}
   {% if (i.bgp_neighbor_passwd is defined) and (i.bgp_neighbor_passwd is not none) -%}
   password             {{ i.bgp_neighbor_passwd }}
   {% endif -%}
   {% if (i.bgp_neighbor_policy_map_in is defined) and (i.bgp_neighbor_policy_map_in is not none) -%}
   bgp-policy-map {{ i.bgp_neighbor_policy_map_in }} in
   {% endif -%}
   {% if (i.bgp_neighbor_policy_map_out is defined) and (i.bgp_neighbor_policy_map_out is not none) -%}
   bgp-policy-map {{ i.bgp_neighbor_policy_map_out }} out
   {% endif -%}
   {% if (i.bgp_neighbor_gnmi_group is defined) and (i.bgp_neighbor_gnmi_group is not none) -%}
   gnmi-sensor-group    {{ i.bgp_neighbor_gnmi_group }}
   !
   {% endif -%}
{% endfor -%}
  !
 !
!
{% endfor -%}
"""
######################################################################
# !!# loopback configuration [9]
######################################################################
loopback_cfg_yaml = """
int_lo:
  1:
    - { ip_addr_v4_w_mask: "107.150.15.1/32", ip_addr_v6_w_mask: , lo_state: "no shutdown" }
  2:
    - { ip_addr_v4_w_mask: "107.150.15.10/32", ip_vrf_fwd: "voice", ip_addr_v6_w_mask: , lo_state: "no shutdown" }
  3:
    - { ip_addr_v4_w_mask: "107.150.15.100/32", ip_vrf_fwd: "unicastvideo", ip_addr_v6_w_mask: , lo_state: "no shutdown" }
"""
######################################################################
# !!# loopback configuration [9]
######################################################################
loopback_cfg_jinja = """
{#
 #################
 # LOOPBACK INT
 #################
-#}
{% for lo in int_lo -%}
interface loopback {{ lo }}
{%- set attr0 = int_lo[lo] %}
{%- for i in attr0 %}
 {% if (i.ip_vrf_fwd is defined) and (i.ip_vrf_fwd is not none) -%}
 ip vrf forwarding {{ i.ip_vrf_fwd }}
 {% endif -%}
 ip address {{ i.ip_addr_v4_w_mask }}
 {% if (i.ip_addr_v6_w_mask is defined) and (i.ip_addr_v6_w_mask is not none) -%}
 ipv6 address {{ i.ip_addr_v6_w_mask }}
 {% endif -%}
 !
 {{ i.lo_state }}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!#  Router w/BGP [10]
######################################################################
rtr_bgp_cfg_yaml = """
router_bgp:
  65501:
    - { redist_map: "out-data", redist_map_static: , graceful_restart_enable: "enable", graceful_restart_stalepath_time: 360, graceful_restart_path_selection_defer_time: , maximum_paths_ebgp: 2 , rtr_id: "107.150.15.1" }
    - { bgp_policy_map: "in-data" }
    - { bgp_rule:  5,  bgp_addr_family: "ipv4-unicast", bgp_addr_prefix_list: "in-data", bgp_addr_comm_list_set: }
    - { bgp_rule: 10, bgp_addr_family: "ipv4-unicast", bgp_addr_action: "deny" }
    - { bgp_neighbor_ipaddr: "107.150.0.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: , bgp_neighbor_update_source: , bgp_neighbor_bfd: ,
        bgp_neighbor_addr_family_details_ipv4_1: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_1: "enable",
        bgp_neighbor_addr_family_details_ipv4_2: "ipv4 multicast", bgp_neighbor_addr_family_state_ipv4_2: "enable",
        bgp_neighbor_addr_family_details_ipv4_3: , bgp_neighbor_addr_family_state_ipv4_3: ,
        bgp_neighbor_addr_family_details_ipv6_1: , bgp_neighbor_addr_family_state_ipv6_1: ,
        bgp_neighbor_addr_family_details_ipv6_2: , bgp_neighbor_addr_family_state_ipv6_2: ,
        bgp_neighbor_addr_family_details_ipv6_3: , bgp_neighbor_addr_family_state_ipv6_3: ,
        bgp_neighbor_addr_family_details_ipv6_4: , bgp_neighbor_addr_family_state_ipv6_4: ,
        bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-data", bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group:  }

    - { bgp_neighbor_ipaddr: "107.150.1.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: , bgp_neighbor_update_source: , bgp_neighbor_bfd: ,
        bgp_neighbor_addr_family_details_ipv4_1: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_1: "enable",
        bgp_neighbor_addr_family_details_ipv4_2: , bgp_neighbor_addr_family_state_ipv4_2: ,
        bgp_neighbor_addr_family_details_ipv4_3: , bgp_neighbor_addr_family_state_ipv4_3: ,
        bgp_neighbor_addr_family_details_ipv6_1: , bgp_neighbor_addr_family_state_ipv6_1: ,
        bgp_neighbor_addr_family_details_ipv6_2: , bgp_neighbor_addr_family_state_ipv6_2: ,
        bgp_neighbor_addr_family_details_ipv6_3: , bgp_neighbor_addr_family_state_ipv6_3: ,
        bgp_neighbor_addr_family_details_ipv6_4: , bgp_neighbor_addr_family_state_ipv6_4: ,
        bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-data", bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group:  }

    - { bgp_neighbor_ipaddr: "107.150.4.0", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: "soft-reconfiguration", bgp_neighbor_update_source: , bgp_neighbor_bfd: ,
        bgp_neighbor_addr_family_details_ipv4_1: "ipv4 multicast", bgp_neighbor_addr_family_state_ipv4_1: "enable",
        bgp_neighbor_addr_family_details_ipv4_2: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_2: "enable",
        bgp_neighbor_addr_family_details_ipv4_3: , bgp_neighbor_addr_family_state_ipv4_3: ,
        bgp_neighbor_addr_family_details_ipv6_1: , bgp_neighbor_addr_family_state_ipv6_1: ,
        bgp_neighbor_addr_family_details_ipv6_2: , bgp_neighbor_addr_family_state_ipv6_2: ,
        bgp_neighbor_addr_family_details_ipv6_3: , bgp_neighbor_addr_family_state_ipv6_3: ,
        bgp_neighbor_addr_family_details_ipv6_4: , bgp_neighbor_addr_family_state_ipv6_4: ,
        bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-data", bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group:  }

    - { bgp_neighbor_ipaddr: "107.150.6.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: "soft-reconfiguration", bgp_neighbor_update_source: , bgp_neighbor_bfd: ,
        bgp_neighbor_addr_family_details_ipv4_1: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_1: "enable",
        bgp_neighbor_addr_family_details_ipv4_2: , bgp_neighbor_addr_family_state_ipv4_2: ,
        bgp_neighbor_addr_family_details_ipv4_3: , bgp_neighbor_addr_family_state_ipv4_3: ,
        bgp_neighbor_addr_family_details_ipv6_1: , bgp_neighbor_addr_family_state_ipv6_1: ,
        bgp_neighbor_addr_family_details_ipv6_2: , bgp_neighbor_addr_family_state_ipv6_2: ,
        bgp_neighbor_addr_family_details_ipv6_3: , bgp_neighbor_addr_family_state_ipv6_3: ,
        bgp_neighbor_addr_family_details_ipv6_4: , bgp_neighbor_addr_family_state_ipv6_4: ,
        bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-data", bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group:  }

    - { bgp_neighbor_ipaddr: "107.150.7.2", bgp_neighbor_remote_as: 100, bgp_neighbor_weight: , soft_reconfiguration: "soft-reconfiguration", bgp_neighbor_update_source: , bgp_neighbor_bfd: ,
        bgp_neighbor_addr_family_details_ipv4_1: "ipv4 unicast", bgp_neighbor_addr_family_state_ipv4_1: "enable",
        bgp_neighbor_addr_family_details_ipv4_2: , bgp_neighbor_addr_family_state_ipv4_2: ,
        bgp_neighbor_addr_family_details_ipv4_3: , bgp_neighbor_addr_family_state_ipv4_3: ,
        bgp_neighbor_addr_family_details_ipv6_1: , bgp_neighbor_addr_family_state_ipv6_1: ,
        bgp_neighbor_addr_family_details_ipv6_2: , bgp_neighbor_addr_family_state_ipv6_2: ,
        bgp_neighbor_addr_family_details_ipv6_3: , bgp_neighbor_addr_family_state_ipv6_3: ,
        bgp_neighbor_addr_family_details_ipv6_4: , bgp_neighbor_addr_family_state_ipv6_4: ,
        bgp_neighbor_passwd: , bgp_neighbor_policy_map_in: "in-data", bgp_neighbor_policy_map_out: , bgp_neighbor_gnmi_group:  }
"""
######################################################################
# !!#  Router w/BGP [10]
######################################################################
rtr_bgp_cfg_jinja = """
{#
 #################
 # ROUTER w/BGP
 #################
-#}
{% for bgp in router_bgp -%}
{% set attrb = router_bgp[bgp] -%}
router bgp {{ bgp }}
 {% for i in attrb -%}
 {% if (i.redist_map is defined) and (i.redist_map is not none) -%}
 redistribute connected redist-map {{ i.redist_map }}
 {% endif -%}
 {% if (i.redist_map_static is defined) and (i.redist_map_static is not none) -%}
 redistribute static redist-map {{ i.redist_map_static }}
 {% endif -%}
 {% if (i.graceful_restart_enable is defined) and (i.graceful_restart_enable is not none) -%}
 graceful-restart          {{ i.graceful_restart_enable }}
 {% endif -%}
 {% if (i.graceful_restart_stalepath_time is defined) and (i.graceful_restart_stalepath_time is not none) -%}
 graceful-restart stalepath-time {{ i.graceful_restart_stalepath_time }}
 {% endif -%}
 {% if (i.graceful_restart_path_selection_defer_time is defined) and (i.graceful_restart_path_selection_defer_time is not none) -%}
 graceful-restart path-selection-defer-time {{ i.graceful_restart_path_selection_defer_time }}
 {% endif -%}
 {% if (i.maximum_paths_ebgp is defined) and (i.maximum_paths_ebgp is not none) -%}
 maximum-paths ebgp {{ i.maximum_paths_ebgp }}
 {% endif -%}
 {% if (i.bgp_policy_map is defined) and (i.bgp_policy_map is not none) -%}
 bgp-policy-map {{ i.bgp_policy_map }}
 {% endif -%}
  {% if (i.bgp_rule is defined) and (i.bgp_rule is not none) -%}
  rule {{ i.bgp_rule }}
   {% if (i.bgp_addr_family is defined) and (i.bgp_addr_family is not none) -%}
   address-family {{ i.bgp_addr_family }}
     {% endif -%}
     {% if (i.bgp_addr_action is defined) and (i.bgp_addr_action is not none) -%}
     {{ i.bgp_addr_action }}
     {% endif -%}
    {% if (i.bgp_addr_prefix_list is defined) and (i.bgp_addr_prefix_list is not none) -%}
    match prefix-list {{ i.bgp_addr_prefix_list }}
    {% endif -%}
    {% if (i.bgp_addr_comm_list is defined) and (i.bgp_addr_comm_list is not none) -%}
    match community-list {{ i.bgp_addr_comm_list }}
    !
    {% endif -%}
    {% if (i.bgp_addr_set_local_pref is defined) and (i.bgp_addr_set_local_pref is not none) -%}
    set local-preference {{ i.bgp_addr_set_local_pref }}
    {% endif -%}
    {% if (i.bgp_addr_comm_list_set is defined) and (i.bgp_addr_comm_list_set is not none) -%}
    set community-list {{ i.bgp_addr_comm_list_set }}
    !
    {% endif -%}
    {% if (i.bgp_addr_set_next_hop is defined) and (i.bgp_addr_set_next_hop is not none) -%}
    set next-hop     {{ i.bgp_addr_set_next_hop }}
    {% endif -%}
   !
  !
 {% if i.bgp_rule == 10 -%}
 !
 {% endif -%}
 {% endif -%}
 {% if (i.bgp_neighbor_ipaddr is defined) and (i.bgp_neighbor_ipaddr is not none) -%}
 neighbor {{ i.bgp_neighbor_ipaddr }}
  {% if (i.bgp_neighbor_remote_as is defined) and (i.bgp_neighbor_remote_as is not none) -%}
  remote-as            {{ i.bgp_neighbor_remote_as }}
  {% endif -%}
  {% if (i.bgp_neighbor_weight is defined) and (i.bgp_neighbor_weight is not none) -%}
  weight               {{ i.bgp_neighbor_weight }}
  {% endif -%}
  {% if (i.soft_reconfiguration is defined) and (i.soft_reconfiguration is not none) -%}
  {{ i.soft_reconfiguration }}
  {% endif -%}
  {% if (i.bgp_neighbor_update_source is defined) and (i.bgp_neighbor_update_source is not none) -%}
  update-source        {{ i.bgp_neighbor_update_source }}
  {% endif -%}
  {% if (i.bgp_neighbor_bfd is defined) and (i.bgp_neighbor_bfd is not none) -%}
  bfd                  {{ i.bgp_neighbor_bfd }}
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv4_1 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_1 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv4_1 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv4_1 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_1 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv4_1 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv4_2 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_2 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv4_2 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv4_2 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_2 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv4_2 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv4_3 is defined) and (i.bgp_neighbor_addr_family_details_ipv4_3 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv4_3 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv4_3 is defined) and (i.bgp_neighbor_addr_family_state_ipv4_3 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv4_3 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv6_1 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_1 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv6_1 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv6_1 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_1 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv6_1 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv6_2 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_2 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv6_2 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv6_2 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_2 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv6_2 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv6_3 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_3 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv6_3 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv6_3 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_3 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv6_3 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_ipv6_4 is defined) and (i.bgp_neighbor_addr_family_details_ipv6_4 is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_ipv6_4 }}
  {% endif -%}
    {% if (i.bgp_neighbor_addr_family_state_ipv6_4 is defined) and (i.bgp_neighbor_addr_family_state_ipv6_4 is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_ipv6_4 }}
  !
  {% endif -%}
  {% if (i.bgp_neighbor_addr_family_details_misc is defined) and (i.bgp_neighbor_addr_family_details_misc is not none) -%}
  address-family {{ i.bgp_neighbor_addr_family_details_misc }}
    {% if (i.bgp_neighbor_addr_family_state_misc is defined) and (i.bgp_neighbor_addr_family_state_misc is not none) -%}
    {{ i.bgp_neighbor_addr_family_state_misc }}
  !
  {% else -%}
  !
  {% endif -%}
  {% endif -%}
  {% if (i.bgp_neighbor_passwd is defined) and (i.bgp_neighbor_passwd is not none) -%}
  password             {{ i.bgp_neighbor_passwd }}
  {% endif -%}
  {% if (i.bgp_neighbor_policy_map_in is defined) and (i.bgp_neighbor_policy_map_in is not none) -%}
  bgp-policy-map {{ i.bgp_neighbor_policy_map_in }} in
  {% endif -%}
  {% if (i.bgp_neighbor_policy_map_out is defined) and (i.bgp_neighbor_policy_map_out is not none) -%}
  bgp-policy-map {{ i.bgp_neighbor_policy_map_out }} out
  {% endif -%}
  {% if (i.bgp_ebgp_multihop is defined) and (i.bgp_ebgp_multihop is not none) -%}
  ebgp-multihop        {{ i.bgp_ebgp_multihop }}
  {% endif -%}
  {% if (i.bgp_neig_desc is defined) and (i.bgp_neig_desc is not none) -%}
  description          "{{ i.bgp_neig_desc }}"
  {% endif -%}
  {% if (i.bgp_neighbor_gnmi_group is defined) and (i.bgp_neighbor_gnmi_group is not none) -%}
  gnmi-sensor-group    {{ i.bgp_neighbor_gnmi_group }}
  {% endif -%}
 !
 {% endif -%}
{% endfor -%}
{% if loop.last -%}
!
{% endif -%}
{% endfor -%}
!
"""
######################################################################
# !!# pim configuration [11]
######################################################################
pim_cfg_yaml = """
##########
# PIM YAML
##########
pim:
  1:
    - { rp_addr: "107.150.0.2",  group_addr_w_mask: "224.0.0.0/4" }
"""
######################################################################
# !!# pim configuration [11]
######################################################################
pim_cfg_jinja = """
{#
 ##############
 # PIM CFG
 ##############
-#}
{% for pm in pim -%}
router pim {{ pm }}
 {% set attrb0 = pim[pm] -%}
 {% for i in attrb0 -%}
 {% if (i.rp_addr is defined) and ( i.rp_addr is not none) and (i.group_addr_w_mask is defined) and (i.group_addr_w_mask is not none) -%}
 rp-address {{ i.rp_addr }} group-address {{ i.group_addr_w_mask }}
{% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# vlan configuration [12]
######################################################################
vlan_cfg_yaml = """
#################
# VLANS - LAG/WAN
#################
vlan_def:
  101:
    - { description: "Subscriber-Facing VLAN on the x/x/gp1 pon", vlan_mode: "ONE2ONE" }
  120:
    - { description: "Data VLAN", l3_service: "ENABLED" }
  121:
    - { description: "SIP VLAN", l3_service: "ENABLED" }
  122:
    - { description: "Multicast Video VLAN", l3_service: "ENABLED" }
  123:
    - { description: "Unicast Video VLAN", l3_service: "ENABLED" }
  220:
    - { description: "Data VLAN", l3_service: "ENABLED" }
  221:
    - { description: "SIP VLAN", l3_service: "ENABLED" }
  222:
    - { description: "Multicast Video VLAN", l3_service: "ENABLED" }
  223:
    - { description: "Unicast Video VLAN", l3_service: "ENABLED" }
"""
######################################################################
# !!# vlan configuration [12]
######################################################################
vlan_cfg_jinja = """
{#
 #################
 # VLANS - LAG/WAN
 #################
-#}
{% for vid in vlan_def -%}
{% set attb0 = vlan_def[vid] -%}
vlan {{ vid }}
 {% for i in attb0 -%}
 {% if (i.vlan_mode is defined) and (i.vlan_mode is not none) -%}
 mode {{ i.vlan_mode }}
 {% endif -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description "{{ i.description }}"
 {% endif -%}
 {% if (i.l3_service is defined) and (i.l3_service is not none) -%}
 l3-service  {{ i.l3_service }}
 {% endif -%}
 {% if (i.egress_flooding is defined) and (i.egress_flooding is not none) -%}
 egress flooding {{ i.egress_flooding }}
 {% endif -%}
 {% if (i.l2_dhcp_profile is defined) and (i.l2_dhcp_profile is not none) -%}
 l2-dhcp-profile {{ i.l2_dhcp_profile }}
 {% endif -%}
 {% if (i.source_verify is defined) and (i.source_verify is not none) -%}
 source-verify   {{ i.source_verify }}
 {% endif -%}
 {% if (i.vlan_mff is defined) and (i.vlan_mff is not none) -%}
 mff             {{ i.vlan_mff }}
{% endif %}
!
{% endfor -%}
{% endfor -%}
"""
######################################################################
# !!# interface vlans [13]
######################################################################
vlan_int_cfg_yaml = """
#################
# VLAN INTERFACE
#################
int_vlan:
  120:
    - { ipaddr_v4_w_mask: "107.150.6.1/24", vlan_state: "no shutdown"  }
  121:
    - { ipaddr_v4_w_mask: "107.151.0.1/30", ip_vrf_fwd: "voice",  vlan_state: "no shutdown"  }
  122:
    - { ipaddr_v4_w_mask: "107.150.0.1/24", ip_pim: 1, vlan_state: "no shutdown"  }
  123:
    - { ipaddr_v4_w_mask: "107.150.1.1/24", ip_vrf_fwd: "unicastvideo",  vlan_state: "no shutdown"  }
  220:
    - { ipaddr_v4_w_mask: "107.150.7.1/24", vlan_state: "no shutdown"  }
  221:
    - { ipaddr_v4_w_mask: "107.151.3.1/24", ip_vrf_fwd: "voice",  vlan_state: "no shutdown"  }
  222:
    - { ipaddr_v4_w_mask: "107.150.4.1/31", ip_pim: 1, vlan_state: "no shutdown"  }
  223:
    - { ipaddr_v4_w_mask: "107.150.5.1/24", ip_vrf_fwd: "unicastvideo",  vlan_state: "no shutdown"  }
"""
######################################################################
# !!# interface vlans [13]
######################################################################
vlan_int_cfg_jinja = """
{#
 #################
 # VLAN INTERFACE
 #################
-#}
{% for vlan in int_vlan -%}
interface vlan {{ vlan }}
 {% set attr0 = int_vlan[vlan] -%}
 {% for i in attr0 -%}
 {% if (i.access_group_ipv4_acl is defined) and (i.access_group_ipv4_acl is not none) -%}
 access-group ipv4-acl {{ i.access_group_ipv4_acl }}
 {% endif -%}
 {% if (i.access_group_ipv6_acl is defined) and (i.access_group_ipv6_acl is not none) -%}
 access-group ipv6-acl {{ i.access_group_ipv6_acl }}
 {% endif -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description "{{ i.description }}"
 {% endif -%}
 {% if (i.mtu is defined) and (i.mtu is not none) -%}
 mtu         {{ i.mtu }}
 {% endif -%}
 {% if (i.proxy_arp is defined) and (i.proxy_arp is not none) -%}
 arp proxy-arp {{ i.proxy_arp }}
 {% endif -%}
 {% if (i.ip_vrf_fwd is defined) and (i.ip_vrf_fwd is not none) -%}
 ip vrf forwarding {{ i.ip_vrf_fwd }}
 {% endif -%}
 {% if (i.ipaddr_vrf_w_mask is defined) and (i.ipaddr_vrf_w_mask is not none) -%}
  ip address {{ i.ipaddr_vrf_w_mask }}
 !
 {% endif -%}
 {% if (i.ipaddr_v4_w_mask is defined) and (i.ipaddr_v4_w_mask is not none) -%}
 ip address {{ i.ipaddr_v4_w_mask }}
 {% endif -%}
 {% if (i.ip_pim is defined) and (i.ip_pim is not none) -%}
 ip pim {{ i.ip_pim }}
 {% endif -%}
 {% if (i.ipaddr_v6_w_mask is defined) and (i.ipaddr_v6_w_mask is not none) -%}
 ipv6 address {{ i.ipaddr_v6_w_mask }}
 {% endif -%}
 {% if (i.ipv6_redirects is defined) and (i.ipv6_redirects is not none) -%}
 ipv6 redirects {{ i.ipv6_redirects }} unreachables {{ i.ipv6_redirects }}
 {% endif -%}
 {% if (i.ipv6_link is defined) and (i.ipv6_link is not none) -%}
 ipv6 {{ i.ipv6_link }} link-mtu {{ i.l3_link_mtu }}
 {% endif -%}
 {% if (i.vlan_state is defined) and (i.vlan_state is not none) -%}
 {{ i.vlan_state }}
{% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# transport-service-profiles [14]
######################################################################
trans_ser_profile_cfg_yaml = """
###########################
# TRANSPORT-SERVICE-PROFILE
###########################
transport_service_profile:
  uplink_lag3:
     - { vlan_list: "120-123", description:  }
  uplink_lag4:
     - { vlan_list: "220-223", description:  }
"""
######################################################################
# !!# transport-service-profiles [14]
######################################################################
trans_ser_profile_cfg_jinja = """
{#
 ###########################
 # TRANSPORT-SERVICE-PROFILE
 ###########################
-#}
{% for tsp in transport_service_profile -%}
{% set attb = transport_service_profile[tsp] -%}
transport-service-profile {{ tsp }}
 {% for i in attb -%}
 {% if (i.description is defined) and ( i.description is not none) -%}
 description {{ i.description | upper }}
 {% endif -%}
 {% if (i.vlan_list is defined) and ( i.vlan_list is not none) -%}
 vlan-list {{ i.vlan_list }}
{% endif -%}
!
{% endfor -%}
{% endfor -%}
"""
######################################################################
# !!# LAG interfaces [15]
######################################################################
lag_int_cfg_yaml = """
###########################
# LAG INTERFACE CONFIG
###########################
int_lag:
 la3:
  - { gnmi_sensor_group: , description: , hash_method: "enhanced", lacp_mode: "active", lacp_actor_key: , mtu: , alarm_suppression: , role: "inni",
      transport_service_profile: "uplink_lag3", transport_service: , vlan_monitor: , gnmi_sensor_group_vlan: , lag_state: "no shutdown" }
 la4:
  - { gnmi_sensor_group: , description: , hash_method: "enhanced", lacp_mode: "active", lacp_actor_key: , mtu: , alarm_suppression: , role: "inni",
      transport_service_profile: "uplink_lag4", transport_service: , vlan_monitor: , gnmi_sensor_group_vlan: , lag_state: "no shutdown" }
"""
######################################################################
# !!# LAG interfaces [15]
######################################################################
lag_int_cfg_jinja = """
{#
 ###########################
 # LAG INTERFACE CONFIG
 ###########################
-#}
{% for lag in int_lag %}
interface lag {{ lag }}
 {% set attr0 = int_lag[lag] -%}
 {% for i in attr0 -%}
 {% if (i.gnmi_sensor_group is defined) and ( i.gnmi_sensor_group is not none) -%}
 gnmi-sensor-group         {{ i.gnmi_sensor_group }}
 {% endif -%}
 {% if (i.description is defined) and ( i.description is not none) -%}
 description               "{{ i.description }}"
 {% endif -%}
 {% if (i.hash_method is defined) and ( i.hash_method is not none) -%}
 hash-method               {{ i.hash_method }}
 {% endif -%}
 {% if (i.lacp_mode is defined) and ( i.lacp_mode is not none) -%}
 lacp-mode                 {{ i.lacp_mode }}
 {% endif -%}
 {% if (i.lacp_actor_key is defined) and ( i.lacp_actor_key is not none) -%}
 lacp-actor-key            {{ i.lacp_actor_key }}
 {% endif -%}
 {% if (i.max_port is defined) and ( i.max_port is not none) -%}
 max-port                  {{ i.max_port }}
 {% endif -%}
 {% if (i.mtu is defined) and ( i.mtu is not none) -%}
 mtu                       {{ i.mtu }}
 {% endif -%}
 {% if (i.role is defined) and ( i.role is not none) -%}
 role                      {{ i.role }}
 {% endif -%}
 {% if (i.transport_service_profile is defined) and ( i.transport_service_profile is not none) -%}
 transport-service-profile {{ i.transport_service_profile }}
 {% endif -%}
 {% if (i.transport_service is defined) and ( i.transport_service is not none) -%}
 transport-service {{ i.transport_service }}
 {% endif -%}
 {%- if (i.vlan_monitor is defined) and ( i.vlan_monitor is not none) %} vlan-monitor      {{ i.vlan_monitor }}
 {% endif -%}
 {%- if (i.gnmi_sensor_group_vlan is defined) and (i.gnmi_sensor_group_vlan is not none) %} gnmi-sensor-group {{ i.gnmi_sensor_group_vlan }}
 !
 {% endif -%}
 {% if (i.shelf_slot is defined) and (i.shelf_slot is not none) -%}
 shelf-slot            {{ i.shelf_slot }}
 {% endif -%}
 {% if (i.lag_state is defined) and ( i.lag_state is not none) -%}
 {{ i.lag_state }}
 {% endif -%}
 {%- endfor %}
!
{%- endfor %}
"""
######################################################################
# !!# interface LAG memebers [16]
######################################################################
lag_mem_cfg_yaml = """
###########################
# ETH INTERFACE CONFIG
###########################
int_eth:
  1/1/x2:
    - { eth_state: "no shutdown", gnmi_sensor: , description: "Lag-member-port for la3", fec: , alarm_suppression: , role: "lag", prot_group: , sys_lag_name: "la3" }
  1/2/x1:
    - { eth_state: "no shutdown", gnmi_sensor: , description: "Lag-member-port for la4", fec: , alarm_suppression: , role: "lag", prot_group: , sys_lag_name: "la4" }
"""
######################################################################
# !!# interface LAG memebers [16]
######################################################################
lag_mem_cfg_jinja = """
{#
 ###########################
 # ETH INTERFACE CONFIG
 ###########################
-#}
{% for eth in int_eth %}
interface ethernet {{ eth }}
 {% set attr0 = int_eth[eth] -%}
 {% for i in attr0 -%}
 {% if (i.alarm_suppression is defined) and (i.alarm_suppression is not none) -%}
 alarm-suppression {{ i.alarm_suppression }}
 {% endif -%}
 {% if (i.arp_announce is defined) and (i.arp_announce is not none) -%}
 arp arp-announce {{ i.arp_announce }}
 {% endif -%}
 {% if (i.arp_ignore is defined) and (i.arp_ignore is not none) -%}
 arp arp-ignore {{ i.arp_ignore }}
 {% endif -%}
 {% if (i.cosq is defined) and (i.cosq is not none) -%}
 cosq              {{ i.cosq }}
 {% endif -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description       "{{ i.description }}"
 {% endif -%}
 {% if (i.fec is defined) and ( i.fec is not none) -%}
 fec               {{ i.fec}}
 {% endif -%}
 {% if (i.gnmi_sensor is defined) and (i.gnmi_sensor is not none) -%}
 gnmi-sensor-group {{ i.gnmi_sensor }}
 {% endif -%}
 {% if (i.ip_unicast_rpf is defined) and (i.ip_unicast_rpf is not none) -%}
 ip-unicast-rpf {{ i.ip_unicast_rpf }}
 {% endif -%}
 {% if (i.lldp_admin_state is defined) and (i.lldp_admin_state is not none) -%}
 lldp admin-state {{ lldp_admin_state }}
 {% endif -%}
 {% if (i.lldp_profile is defined) and (i.lldp_profile is not none) -%}
 lldp profile LLDP-CORE
 {% endif -%}
 {% if (i.eth_state is defined) and (i.eth_state is not none) -%}
 {{ i.eth_state }}
 {% endif -%}
 {% if (i.switch_port is defined) and (i.switch_port is not none) -%}
 switchport  {{ i.switch_port }}
 {% endif -%}
 {% if (i.prot_group is defined) and (i.prot_group is not none) -%}
 protection-group  {{ i.prot_group }}
 {% endif -%}
 {% if (i.role is defined) and ( i.role is not none) -%}
 role              {{ i.role }}
 {% endif -%}
 {% if (i.transport_service_profile is defined) and (i.transport_service_profile is not none) -%}
 transport-service-profile              {{ i.transport_service_profile }}
 {% endif -%}
 {% if (i.sys_lag_name is defined) and (i.sys_lag_name is not none) -%}
 system-lag        {{ i.sys_lag_name }}
 {% endif -%}
 {% if (i.slot_lag is defined) and (i.slot_lag is not none) -%}
 slot-lag        {{ i.slot_lag }}
{% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# grade-of-service [17]
######################################################################
gos_cfg_yaml = """
###########################
# GRADE OF SERVICE CONFIG
###########################
grade_of_service:
 - "ont-ethernet-gos-profile ont-eth-pm"
 - "bin-gos upstream-oversize-packets"
 - "threshold 10"
 - "tca-name Upstream_Oversize"
"""
######################################################################
# !!# grade-of-service [17]
######################################################################
gos_cfg_jinja = """
{#
 ###########################
 # GRADE OF SERVICE CONFIG
 ###########################
-#}
grade-of-service
{% for gos in grade_of_service -%}
{{ gos }}
{% if loop.last -%}
!
{% endif -%}
{% endfor-%}
!
!
"""
######################################################################
# !!# rg-mgmt-profile [18]
######################################################################
rg_mgmt_profile_cfg_yaml = """
###########################
# RG-MGMT-PROFILE CONFIG
###########################
rg_profile:
  rg-mgmt-1:
    - { acs_url: "https://my.fqdn.com", sys_username: "sys-admin", sys_password: "sys-admin" }
"""
######################################################################
# !!# rg-mgmt-profile [18]
######################################################################
rg_mgmt_profile_cfg_jinja = """
{#
 ###########################
 # RG-MGMT-PROFILE CONFIG
 ###########################
-#}
{% for rg in rg_profile -%}
rg-mgmt-profile {{ rg }}
 {% set att0 = rg_profile[rg] -%}
 {% for i in att0 -%}
 {% if (i.acs_url is defined) and (i.acs_url is not none) -%}
 acs-url {{ i.acs_url }}
 {% endif -%}
 {% if (i.sys_username is defined) and (i.sys_username is not none) -%}
 username {{ i.sys_username }}
 {% endif -%}
 {% if (i.sys_password is defined) and (i.sys_password is not none) -%}
 password {{ i.sys_password }}
 {% endif -%}
!
{% endfor -%}
{% endfor -%}

"""
######################################################################
# !!# class-maps [19]
######################################################################
classmap_cfg_yaml = """
#############
# CLASS-MAPS
#############
class_map:                                                                                                                                                                                                                 
  ip all_service:
    # -----------
    # INGRESS
    # -----------
    - { fn_desc: "DHCP and ARP", direction: "ingress", flow_number: 1 }
    - rule:
      - { number: 1, match_detail: "ethertype ARP" }
      - { number: 2, match_detail: "protocol UDP destination-port-range BOOTPS" }
    - { fn_desc: "ICMP", direction: "ingress", flow_number: 2 }
    - rule:
      - { number: 1, match_detail: "protocol ICMP destination-ipv4-prefix-list local_interfaces" }
        #- { number: 2, match_detail: "protocol IPV6-ICMP destination-ipv6-prefix-list ALL_LOCAL_IPv6" }
    - { fn_desc: "DNS", direction: "ingress", flow_number: 3 }
    - rule:
       - { number: "1", match_detail: "destination-port-range DOMAIN" }
    - { fn_desc: "NTP", direction: "ingress", flow_number: 4 }
    - rule:
       - { number: "1", match_detail: "destination-port-range 123" }
    - { fn_desc: "Voice", direction: "ingress", flow_number: 8 }
    - rule:
       - { number: "1", match_detail: "source-ipv4-prefix-list voip_subscriber_network" }
    - { fn_desc: "IGMP", direction: "ingress", flow_number: 9 }
    - rule:
       - { number: "1", match_detail: "protocol IGMP" }
    - { fn_desc: "allowed VOD List", direction: "ingress", flow_number: 11 }
    - rule:
       - { number: "1", match_detail: "destination-ipv4-prefix-list vod_server" }
    - { fn_desc: "Allow All Traffic", direction: "ingress", flow_number: 15 }
    - rule:
       - { number: "1", match_detail: "destination-ip-network 0.0.0.0/0" }
    # -----------
    # EGRESS
    # -----------
    - { fn_desc: "ARP and DHCP", direction: "egress", flow_number: 1 }
    - rule:
       - { number: "1", match_detail: "ethertype ARP" }
       - { number: "2", match_detail: "destination-port-range BOOTPC" }
      #- { number: "3", match_detail: "protocol udp destination-port-range dhcpv6-client" }
    - { fn_desc: "ICMP", direction: "egress", flow_number: 2 }
    - rule:
       - { number: "1", match_detail: "source-ipv4-prefix-list local_interfaces" }
      #- { number: "2", match_detail: "protocol ipv6-icmp" }
    - { fn_desc: "DNS", direction: "egress", flow_number: 3 }
    - rule:
       - { number: "1", match_detail: "source-port-range DOMAIN" }
    - { fn_desc: "NTP", direction: "egress", flow_number: 4 }
    - rule:
       - { number: "1", match_detail: "source-port-range 123" }
    - { fn_desc: "Voice", direction: "egress", flow_number: 8 }
    - rule:
       - { number: "1", match_detail: "destination-ipv4-prefix-list voip_subscriber_network" }
    - { fn_desc: "IGMP", direction: "egress", flow_number: 9 }
    - rule:
       - { number: "1", match_detail: "protocol IGMP" }
    - { fn_desc: "allowed VOD List", direction: "egress", flow_number: 11 }
    - rule:
       - { number: "1", match_detail: "source-ipv4-prefix-list vod_server" }
    - { fn_desc: "ANY", direction: "egress", flow_number: 15 }
    - rule:
       - { number: "1", match_detail: "source-ip-network 0.0.0.0/0" }
  ip fallback_class_map:
    # -----------
    # INGRESS
    # -----------
    - {fn_desc: "fallback in", direction: "ingress", flow_number: 1 }
    - rule:
       - { number: "1", match_detail: "destination-ip-network 0.0.0.0/0" }
    # -----------
    # EGRESS
    # -----------
    - {fn_desc: "fallback out", direction: "egress", flow_number: 1 }
    - rule:
       - { number: "1", match_detail: "source-ip-network 0.0.0.0/0" }
  ip initial_class_map:
    # -----------
    # INGRESS
    # -----------
    - { fn_desc: "DHCP (in)", direction: "ingress", flow_number: 1 }
    - rule:
      - { number: 1, match_detail: "protocol UDP destination-port-range BOOTPS" }
    - { fn_desc: "ARP (in)", direction: "ingress", flow_number: 2 }
    - rule:
      - { number: 1, match_detail: "ethertype ARP" }
    # -----------
    # EGRESS
    # -----------
    - { fn_desc: "DHCP (out)", direction: "egress", flow_number: 1 }
    - rule:
      - { number: 1, match_detail: "protocol UDP destination-port-range BOOTPC" }
"""
######################################################################
# !!# class-maps [19]
######################################################################
classmap_cfg_jinja = """
{#
 #############
 # CLASS-MAPS
 #############
-#}
{% for fn in class_map -%}
class-map {{ fn }}
 {% set elem = class_map[fn] -%}
 {% for i in elem -%}
 {% if (i.rl_state is defined) and (i.rl_state is not none) -%}
 resource-level {{ i.rl_state }}
 {% else -%}
 {% endif -%}
 {% if (i.direction is defined) and not none -%}
 {{ i.direction }}-flow {{ i.flow_number }}
 {% else -%}
 {% if (i.flow_number is defined) and not none -%}
 flow {{ i.flow_number }}
 {% endif -%}
 {% endif -%}
  {% if (i.fn_desc is defined) and (i.fn_desc is not none) -%}
  description "{{ i.fn_desc }}"
  {% endif -%}
  {% for x in i.rule -%}
  rule {{ x.number }} match {{ x.match_detail }}
  {% if loop.last -%}
 !
 {% endif -%}
 {% endfor -%}
 {%- endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# policy-maps [20]
######################################################################
policymap_cfg_yaml = """
################
# POLICY-MAP CFG
################
policy_map:
  fallback_policy_map:
   - { class_map_ip: "fallback_class_map" }
   - { egress_flow_no: 1 }
   - { ingress_flow_no: 1 }

  initial_policy_map:
   - { class_map_ip: "initial_class_map" }
   - { egress_flow_no: 1 }
   - { ingress_flow_no: 1, ingress_meter_eir: 64 }
   - { ingress_flow_no: 2, ingress_meter_eir: 64 }

  policy_map-hsi_100m:
   - { class_map_ip: "all_service" }
   - { traffic_class: 1, egress_shaper: "yes", es_max: 100000 }
   - { traffic_class: 2, egress_shaper: "yes", es_max: 64 }
   - { egress_flow_no: 1 , traffic_class_sub: 2}
   - { egress_flow_no: 2 , traffic_class_sub: 2}
   - { egress_flow_no: 3 , traffic_class_sub: 2}
   - { egress_flow_no: 4 , traffic_class_sub: 2}
   - { egress_flow_no: 15 , traffic_class_sub: 1}
   - { ingress_flow_no: 1 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 2 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 3 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 4 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 15 , ingress_meter_eir: 100000, ingress_meter_ebs: 10000 }
   - { egress: "shaper", scheduling_type: "2SP-6WRR", egress_bw: , ebm_parent_cos: "cos2", ebm_parent_cos_min: , ebm_parent_max: "300000", ebm_parent_min: "0",
       eb_min_max_parent_cos: , eb_min_parent_cos: , eb_min_parent_max: , eb_min_parent_weight:  }

  policy_map-video:
   - { class_map_ip: "all_service" }
   - { traffic_class: 1 }
   - { traffic_class: 2, egress_shaper: "yes", es_max: 64, es_min: 64}
   - { egress_flow_no: 1 , traffic_class_sub: 2}
   - { egress_flow_no: 2 , traffic_class_sub: 2}
   - { egress_flow_no: 3 , traffic_class_sub: 2}
   - { egress_flow_no: 4 , traffic_class_sub: 2}
   - { egress_flow_no: 9 , traffic_class_sub: 2}
   - { egress_flow_no: 11 , traffic_class_sub: 1}
   - { egress_flow_no: 15 , traffic_class_sub: 1}
   - { ingress_flow_no: 1 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 2 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 3 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 4 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 9 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 11, ingress_meter_cir: 64, ingress_meter_cbs: 20000, ingress_meter_ebs: 20000, ingress_meter_eir: 10000 }
   - { ingress_flow_no: 15 , ingress_meter_eir: 100000, ingress_meter_ebs: 10000 }
   - { egress: "shaper", scheduling_type: "2SP-6WRR", egress_bw: , ebm_parent_cos: "cos3", ebm_parent_cos_min: "cos2", ebm_parent_max: "100000", ebm_parent_min: "20000",
       eb_min_max_parent_cos: , eb_min_parent_cos: , eb_min_parent_max: , eb_min_parent_weight:  }

  policy_map-voice:
   - { class_map_ip: "all_service" }
   - { traffic_class: 1, egress_shaper: "yes", es_max: 512, es_min: 512}
   - { traffic_class: 2, egress_shaper: "yes", es_max: 64, es_min: 64}
   - { egress_flow_no: 1 , traffic_class_sub: 2}
   - { egress_flow_no: 2 , traffic_class_sub: 2}
   - { egress_flow_no: 3 , traffic_class_sub: 2}
   - { egress_flow_no: 4 , traffic_class_sub: 2}
   - { egress_flow_no: 8 , traffic_class_sub: 1}
   - { egress_flow_no: 15 , egress_action: "deny"}
   - { ingress_flow_no: 1 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 2 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 3 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 4 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 9 , ingress_meter_cir: 64, ingress_meter_cbs: 20000 }
   - { ingress_flow_no: 11, ingress_meter_cir: 64, ingress_meter_cbs: 20000, ingress_meter_ebs: 20000, ingress_meter_eir: 10000 }
   - { ingress_flow_no: 15 , ingress_action: "deny" }
   - { egress: "shaper", scheduling_type: , egress_bw: , ebm_parent_cos: "cos7", ebm_parent_cos_min: , ebm_parent_max: "768", ebm_parent_min: "768",
       eb_min_max_parent_cos: , eb_min_parent_cos: , eb_min_parent_max: , eb_min_parent_weight:  }
"""
######################################################################
# !!# policy-map [20]
######################################################################
policymap_cfg_jinja = """
{#
 ################
 # POLICY-MAP CFG
 ################
-#}
{%  for pm in policy_map -%}
{% set attb = policy_map[pm] -%}
policy-map {{ pm }}
 {% for i in attb -%}
 {% if (i.policy_actions is defined) and ( i.policy_actions is not none) -%}
 policy-actions {{ i.policy_actions }}
 {% endif -%}
 {% if (i.class_map_ether is defined) and ( i.class_map_ether is not none) -%}
 class-map-ethernet {{ i.class_map_ether }}
  flow {{ i.class_map_ether_flow }}
  !
 {% endif -%}
 {% if (i.class_map_ip is defined) and ( i.class_map_ip is not none) -%}
 class-map-ip {{ i.class_map_ip }}
  {% endif -%}
  {% if (i.traffic_class is defined) and ( i.traffic_class is not none) -%}
  traffic-class {{ i.traffic_class }}
   {% if (i.egress_shaper is defined) and ( i.egress_shaper == "yes" ) -%}
   {% if (i.es_max is defined) and ( i.es_max is not none) -%}
   egress-shaper maximum {{ i.es_max }}
   {% endif -%}
   {% if (i.es_min is defined) and ( i.es_min is not none) -%}
   egress-shaper minimum {{ i.es_min }}
   {% endif -%}
   {% if (i.es_depth is defined) and ( i.es_depth is not none) -%}
   egress-shaper queue-depth {{ i.es_depth }}
   {% endif -%}
   {% if (i.es_policy is defined) and ( i.es_policy is not none) -%}
   egress-shaper discard-policy {{ i.es_policy }}
  {% endif -%}
  !
  {% else -%}
  !
  {% endif -%}
  {% endif -%}
  {% if (i.egress_flow_no is defined) and (i.egress_flow_no is not none) -%}
  egress-flow {{ i.egress_flow_no }}
   {% if (i.traffic_class_sub is defined) and ( i.traffic_class_sub is not none) -%}
   traffic-class {{ i.traffic_class_sub }}
   {% endif -%}
   {% if (i.eg_account is defined) and (i.eg_account is not none) -%}
   {{ i.eg_account }}
   {% endif -%}
   {% if (i.egress_meter_cir is defined) and (i.egress_meter_cir is not none) -%}
   egress-meter cir {{ i.egress_meter_cir }}
   {% endif -%}
   {% if (i.egress_meter_eir is defined) and (i.egress_meter_eir is not none) -%}
   egress-meter eir {{ i.egress_meter_eir }}
   {%  endif -%}
   {% if (i.egress_action is defined) and (i.egress_action is not none) -%}
   {{ i.egress_action }}
  {% endif -%}
  !
  {% endif -%}
  {% if (i.ingress_flow_no is defined) and (i.ingress_flow_no is not none) -%}
  ingress-flow {{ i.ingress_flow_no }}
   {% if (i.ig_account is defined) and (i.ig_account is not none) -%}
   {{ i.ig_account }}
   {% endif -%}
   {% if (i.ingress_meter_cir is defined) and (i.ingress_meter_cir is not none) -%}
   ingress-meter cir {{ i.ingress_meter_cir }}
   {% endif -%}
   {% if (i.ingress_meter_eir is defined) and (i.ingress_meter_eir is not none) -%}
   ingress-meter eir {{ i.ingress_meter_eir }}
   {%  endif  -%}
   {% if (i.ingress_meter_cbs is defined) and (i.ingress_meter_cbs is not none) -%}
   ingress-meter cbs-bytes {{ i.ingress_meter_cbs }}
   {% endif -%}
   {% if (i.ingress_meter_ebs is defined) and (i.ingress_meter_ebs is not none) -%}
   ingress-meter ebs-bytes {{ i.ingress_meter_ebs }}
   {% endif -%}
   {% if (i.ingress_action is defined) and (i.ingress_action is not none) -%}
   {{ i.ingress_action }}
  {% endif -%}
  !
  {% endif -%}
  {% if (i.egress is defined) and (i.egress == "shaper") -%}
  egress {{ i.egress }}
   {% if (i.scheduling_type is defined) and ( i.scheduling_type is not none) -%}
   scheduling-type {{ i.scheduling_type }}
   {% endif -%}
   {% if (i.egress_bw is defined) and ( i.egress_bw is not none) -%}
   bw {{ i.egress_bw }}
   {% endif -%}
    {% if (i.ebm_parent_cos is defined) and ( i.ebm_parent_cos is not none) -%}
    max-parent-cos {{ i.ebm_parent_cos }}
    {% endif -%}
    {% if (i.ebm_parent_cos_min is defined) and ( i.ebm_parent_cos_min is not none) -%}
    min-parent-cos {{ i.ebm_parent_cos_min }}
    {% endif -%}
    {% if (i.ebm_parent_max is defined) and ( i.ebm_parent_max is not none) -%}
    maximum        {{ i.ebm_parent_max }}
    {% endif -%}
    {% if (i.ebm_parent_min is defined) and ( i.ebm_parent_min is not none) -%}
    minimum        {{ i.ebm_parent_min }}
   {% endif -%}
   {%  if (i.eb_min is defined) and ( i.eb_min is not none) -%}
   bw {{ i.eb_min }}
   {% endif -%}
    {% if (i.eb_min_max_parent_cos is defined) and ( i.eb_min_max_parent_cos is not none) -%}
    max-parent-cos {{ i.eb_min_max_parent_cos }}
    {% endif -%}
    {% if (i.eb_min_parent_cos is defined) and ( i.eb_min_parent_cos is not none) -%}
    min-parent-cos {{ i.eb_min_parent_cos }}
    {% endif -%}
    {% if (i.eb_min_parent_max is defined) and ( i.eb_min_parent_max is not none) -%}
    maximum {{ i.eb_min_parent_max }}
    {% endif -%}
    {% if (i.eb_min_parent_min is defined) and ( i.eb_min_parent_min is not none) -%}
    minimum         {{ i.eb_min_parent_min }}
   {% endif -%}
    {% if (i.eb_min_parent_weight is defined) and ( i.eb_min_parent_weight is not none) -%}
    weight {{ i.eb_min_parent_weight }}
   {% endif -%}
  !
  {% endif -%}
  {% if (i.ingress_misc is defined) and (i.ingress_misc is not none) -%}
  ingress {{ i.ingress_misc }}
   {% if (i.ingress_misc_eir is defined) and ( i.ingress_misc_eir is not none) -%}
   eir       {{ i.ingress_misc_eir }}
  {% endif -%}
  !
  {% endif -%}
  {% if (i.egress_aggregate_shaper is defined) and (i.egress_aggregate_shaper is not none) -%}
  egress-aggregate-shaper {{ i.egress_aggregate_shaper }}
 {% endif -%}
 {% if loop.last -%}
 !
{% endif -%}
{%  endfor -%}
!
{% endfor -%}
"""
######################################################################
# !!# dhcp and multibind [21]
######################################################################
mb_dhcp_cfg_yaml = """
################
# MULTIBIND INT
################
int_mb:
  datamb:
    - { description: "multibind for data & mcast on default VRF", ip_addr_v4_w_mask: "107.150.16.1/20", ip_addr_v6_w_mask: , proxy_arp: , mb_state: "no shutdown" }
  videomb:
    - { ip_vrf: "unicastvideo", ip_addr_v4_w_mask_vrf: "107.150.128.1/20", description: "multibind for unicast video", proxy_arp: , mb_state: "no shutdown" }
  voicemb:
    - { ip_vrf: "voice", ip_addr_v4_w_mask_vrf: "10.128.128.25/29", description: "multibind for voice", proxy_arp: , mb_state: "no shutdown"}
################
# DHCP RELAY CFG
################
dhcp_relay_server:
  hsi:
   - { helper_no: 1, helper_addr: "20.10.30.39" }
   - { helper_no: 2, helper_addr: "20.10.30.40" }
   - { relay_addr: "10.30.60.1", l2_dhcp_profile: "l2-dhcp-prof-1" }
  video:
   - { helper_no: 1, helper_addr: "30.10.30.39" }
   - { relay_addr: "10.30.70.1", vrf: "unicastvideo", l2_dhcp_profile: "l2-dhcp-prof-1" }
  voice:
   - { helper_no: 1, helper_addr: "40.10.30.39" }
   - { relay_addr: "10.30.70.1", vrf: "voice", l2_dhcp_profile: "l2-dhcp-prof-1" }
"""
######################################################################
# !!# dhcp and multibind [21]
######################################################################
mb_dhcp_cfg_jinja = """
{#
 ################
 # MULTIBIND INT
 ################
-#}
{% for mb in int_mb -%}
interface multibind {{ mb }}
{%- set attr0 = int_mb[mb] %}
{%- for i in attr0 %}
 {% if (i.ip_addr_v4_w_mask is defined) and (i.ip_addr_v4_w_mask is not none) -%}
 ip address {{ i.ip_addr_v4_w_mask }}
 {% endif -%}
 {% if (i.ip_addr_v6_w_mask is defined) and (i.ip_addr_v6_w_mask is not none) -%}
 ipv6 address {{ i.ip_addr_v6_w_mask }}
 {% endif -%}
 {% if (i.proxy_arp is defined) and (i.proxy_arp is not none) -%}
 arp proxy-arp {{ i.proxy_arp }}
 {% endif -%}
 {% if (i.ip_vrf is defined) and (i.ip_vrf is not none) -%}
 ip vrf forwarding {{ i.ip_vrf }}
   ip address {{ i.ip_addr_v4_w_mask_vrf }}
 !
 {% endif -%}
 {% if (i.ipv6_enabled is defined) and (i.ipv6_enabled is not none) -%}
 ipv6 enabled {{ i.ipv6_enabled }}
 {% endif -%}
 {% if (i.description is defined) and (i.description is not none) -%}
 description "{{ i.description }}"
 {% endif -%}
 {% if (i.mb_state is defined) and (i.mb_state is not none) -%}
 {{ i.mb_state }}
{% endif -%}
{% endfor -%}
{% if loop.cycle -%}
!
{% endif -%}
{% endfor -%}
{#
 ################
 # FIXED CFG
 ################
-#}
id-profile id-prof-1
circuit-id "%SystemId Eth %Shelf/%Slot/%Port/%OntPort:%CTag"
remote-id %OntIfSID
!
l2-dhcp-profile l2-dhcp-prof-1
id-name id-prof-1
!
{#
 ################
 # DHCP RELAY CFG
 ################
-#}
{% for dv4r in dhcp_relay_server -%}
dhcp-v4-relay-profile {{ dv4r }}
 {% set attrb0 = dhcp_relay_server[dv4r] -%}
 {% for i in attrb0 -%}
 {% if (i.helper_no is defined) and (i.helper_addr is defined) and (i.helper_addr is not none) -%}
 helper-address {{ i.helper_no }} {{ i.helper_addr }}
 {% endif -%}
 {% if (i.relay_addr is defined) and (i.relay_addr is not none) -%}
 relay-agent-address {{ i.relay_addr }}
 {% endif -%}
 {% if (i.vrf is defined) and (i.vrf is not none) -%}
 vrf {{ i.vrf }}
 {% endif -%}
 {% if (i.l2_dhcp_profile is defined) and (i.l2_dhcp_profile is not none) -%}
 l2-dhcp-profile {{ i.l2_dhcp_profile }}
{% endif -%}
{% endfor -%}
!
{% endfor -%}
"""
#######################
list_of_yaml = [
basic_settings_yaml,
prefix_list_yaml,
access_list_yaml,
cos_cosq_profiles_yaml,
out_of_band_mgmt_yaml,
cntrl_plane_yaml,
redist_cfg_yaml,
vrf_cfg_yaml,
loopback_cfg_yaml,
rtr_bgp_cfg_yaml,
pim_cfg_yaml,
vlan_cfg_yaml,
vlan_int_cfg_yaml,
trans_ser_profile_cfg_yaml,
lag_int_cfg_yaml,
lag_mem_cfg_yaml,
gos_cfg_yaml,
rg_mgmt_profile_cfg_yaml,
classmap_cfg_yaml,
policymap_cfg_yaml,
mb_dhcp_cfg_yaml,
]
#######################
list_of_jinja = [
basic_settings_jinja,
prefix_list_jinja,
access_list_jinja,
cos_cosq_profiles_jinja,
out_of_band_mgmt_jinja,
cntrl_plane_jinja,
redist_cfg_jinja,
vrf_cfg_jinja,
loopback_cfg_jinja,
rtr_bgp_cfg_jinja,
pim_cfg_jinja,
vlan_cfg_jinja,
vlan_int_cfg_jinja,
trans_ser_profile_cfg_jinja,
lag_int_cfg_jinja,
lag_mem_cfg_jinja,
gos_cfg_jinja,
rg_mgmt_profile_cfg_jinja,
classmap_cfg_jinja,
policymap_cfg_jinja,
mb_dhcp_cfg_jinja,
]

###############################################################################
# START INPUT VARIABLES
#DEVICE_DICT = {
#    'host': input('Enter target E9 hostname or ipaddr: '),
#    'username': input('Enter ssh login username: '),
#    'password': gp('Enter ssh login password: '),
#    'device_type': 'vyos'
#}
#
#J2_FILE = input('Enter jinja2 [*.j2] filename [with absolute path]: ')
#J2_YAML = input('Enter yaml [*.yaml or *.yml] filename [with absolute path]: ')
# END INPUT VARIABLES
###############################################################################


###############################################################################
# Function [0] to setup logging
###############################################################################
def init_logger():
    """
    DEFINE LOGGER FUNCTIONS
    """
    from logging.config import dictConfig
    logging_config = dict(
        version=1,
        formatters={
            "format_f": {
                "format": "%(asctime)s %(name)-10s %(levelname)-6s %(message)s"
            }
        },
        handlers={
            "handler_h": {
                "class": "logging.StreamHandler",
                "formatter": "format_f",
                "level": logging.INFO,
            }
        },
        root={
            "handlers": ["handler_h"],
            "level": logging.DEBUG,
        },
    )
    dictConfig(logging_config)
    logger = logging.getLogger()
    logging.getLogger("netmiko").setLevel(logging.WARNING)
    if logger:
        return True


###############################################################################
# Function [1]  Generate Template
###############################################################################
def gen_tmpl(jinja2_file, yaml_file):
    """
    GENERATE CONFIGURATION STANZAS WITH JINJA2
    """
    with open(jinja2_file, 'r') as jfile:
        tfile = jfile.read()
    template = jinja2.Template(tfile)
    with open(yaml_file, 'r') as yml_file:
        var_influx = yaml.load(yml_file, yaml.FullLoader)
    try:
        cfg_list = template.render(var_influx)
    except jinja2.TemplateError as err:
        logging.info("Jinja2 render failed: Review yaml and Jinja files.")
        sys.exit(u'Template Error: {}'.format(err.message))
    return cfg_list


###############################################################################
# Function [1]  Generate Template
###############################################################################
def gen_tmpl_direct(jinja_txt, yml_txt):
    """
    GENERATE CONFIGURATION STANZAS WITH JINJA2
    """
    template = jinja2.Template(jinja_txt)
    var_influx = yaml.load(yml_txt, yaml.FullLoader)
    try:
        cfg_list = template.render(var_influx)
    except jinja2.TemplateError as err:
        logging.info("Jinja2 render failed: Review yaml and Jinja files.")
        sys.exit(u'Template Error: {}'.format(err.message))
    return cfg_list


###############################################################################
# Function [2] Connect via ssh (netmiko) and execute/send/save cfg commands
###############################################################################
def send_cfg_cmds(target_device, command):
    """
    ENTER CFG MODE SEND AND SAVE CONFIGURATION [COMMAND]
    """
    try:
        with ConnectHandler(**target_device) as ssh:
            prompt = ssh.find_prompt()
            logging.info("The E9 system being updated is: {}".format(prompt))
            cfg_mode = ssh.send_command_timing(
                command_string='configure',
                strip_prompt=False,
                strip_command=False)
            if "config" in cfg_mode:
                cfg_mode += ssh.send_command_timing(command)
            if "config" in cfg_mode:
                cfg_mode += ssh.send_command_timing(
                    command_string='end',
                    strip_prompt=False,
                    strip_command=False)
            if "{}".format(prompt) in cfg_mode:
                cfg_mode += ssh.send_command_timing(
                    command_string='copy running-config startup-config',
                    strip_prompt=False,
                    strip_command=False)
            ssh.disconnect()
            return cfg_mode

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        logging.info(error)


###############################################################################
# Function [3] Use a menu to drive selections
###############################################################################
def list():
    """
    MENU/LIST OF ACTIONS
    """
    operation = input('''
Select operation:
[1] Print the basic-settings reference configuration
[2] Print the prefix-lists reference configuration
[3] Print the access-lists reference configuration
[4] Print the cos cosq-profile reference configuration
[5] Print the out-of-band management reference configuration
[6] Print the control-plane reference configuration
[7] Print the redirect reference configuration
[8] Print the vrf reference configuration
[9] Print the loopback interface reference configuration
[10] Print the router/bgp reference configuration
[11] Print the pim reference configuration
[12] Print the vlan assignment reference configuration
[13] Print the vlan interface reference configuration
[14] Print the transport profile reference configuration
[15] Print the lag interface reference configuration
[16] Print the interface lag member reference configuration
[17] Print the grade-of-service reference configuration
[18] Print the rg-mgmt-profile reference configuration
[19] Print the class-map reference configuration
[20] Print the policy-map reference configuration
[21] Print the dhcp and multibind interface reference configuration
[29] Print the entire reference configuration
[30] Display list

''')

    if operation == '1':
        gen_basic_cfg = gen_tmpl_direct(basic_settings_jinja,
                                        basic_settings_yaml)
        print(
            "#" * 4 +
            " E9-2 L3 IPv4 3-Play Reference Configuration [!!basic-settings] "
            + "#" * 4)
        print(gen_basic_cfg)
        print("#" * 70)

    elif operation == '2':
        gen_prefix_cfg = gen_tmpl_direct(prefix_list_jinja, prefix_list_yaml)
        print("#" * 25 + " AXOS REF PREFIX CFG " + "#" * 25)
        print(gen_prefix_cfg)
        print("#" * 70)

    elif operation == '3':
        gen_acl_cfg = gen_tmpl_direct(access_list_jinja, access_list_yaml)
        print("#" * 25 + " AXOS REF ACCESS-LIST CFG " + "#" * 20)
        print(gen_acl_cfg)
        print("#" * 70)

    elif operation == '4':
        gen_cos_cfg = gen_tmpl_direct(cos_cosq_profiles_jinja,
                                      cos_cosq_profiles_yaml)
        print("#" * 25 + " AXOS REF COS COSQ PROFILES CFG " + "#" * 15)
        print(gen_cos_cfg)
        print("#" * 70)

    elif operation == '5':
        gen_oob_cfg = gen_tmpl_direct(out_of_band_mgmt_jinja,
                                      out_of_band_mgmt_yaml)
        print("#" * 23 + " AXOS REF OOB MGMT CFG " + "#" * 23)
        print(gen_oob_cfg)
        print("#" * 70)

    elif operation == '6':
        gen_cplane_cfg = gen_tmpl_direct(cntrl_plane_jinja, cntrl_plane_yaml)
        print("#" * 22 + " AXOS REF CONTROL-PLANE MGMT CFG " + "#" * 22)
        print(gen_cplane_cfg)
        print("#" * 70)

    elif operation == '7':
        gen_rdist_cfg = gen_tmpl_direct(redist_cfg_jinja, redist_cfg_yaml)
        print("#" * 23 + " AXOS REF REDISTRIBUTION CFG " + "#" * 23)
        print(gen_rdist_cfg)
        print("#" * 70)

    elif operation == '8':
        gen_vrf_cfg = gen_tmpl_direct(vrf_cfg_jinja, vrf_cfg_yaml)
        print("#" * 25 + " AXOS REF VRF CFG " + "#" * 25)
        print(gen_vrf_cfg)
        print("#" * 70)

    elif operation == '9':
        gen_lo_cfg = gen_tmpl_direct(loopback_cfg_jinja, loopback_cfg_yaml)
        print("#" * 25 + " AXOS REF LOOPBACK CFG " + "#" * 25)
        print(gen_lo_cfg)
        print("#" * 70)

    elif operation == '10':
        gen_rtr_cfg = gen_tmpl_direct(rtr_bgp_cfg_jinja, rtr_bgp_cfg_yaml)
        print("#" * 25 + " AXOS REF ROUTER/BGP CFG " + "#" * 25)
        print(gen_rtr_cfg)
        print("#" * 70)

    elif operation == '11':
        gen_pim_cfg = gen_tmpl_direct(pim_cfg_jinja, pim_cfg_yaml)
        print("#" * 25 + " AXOS REF ROUTER/PIM CFG " + "#" * 25)
        print(gen_pim_cfg)
        print("#" * 70)

    elif operation == '12':
        gen_vlan_cfg = gen_tmpl_direct(vlan_cfg_jinja, vlan_cfg_yaml)
        print("#" * 25 + " AXOS REF VLAN CFG " + "#" * 25)
        print(gen_vlan_cfg)
        print("#" * 70)

    elif operation == '13':
        gen_vlan_int_cfg = gen_tmpl_direct(vlan_int_cfg_jinja, vlan_int_cfg_yaml)
        print("#" * 25 + " AXOS REF VLAN INTERFACE CFG " + "#" * 25)
        print(gen_vlan_int_cfg)
        print("#" * 70)

    elif operation == '14':
        gen_trans_cfg = gen_tmpl_direct(trans_ser_profile_cfg_jinja, trans_ser_profile_cfg_yaml )
        print("#" * 25 + " AXOS REF TRANSPORT PROFILE CFG " + "#" * 25)
        print(gen_trans_cfg)
        print("#" * 70)

    elif operation == '15':
        gen_lag_cfg = gen_tmpl_direct(lag_int_cfg_jinja, lag_int_cfg_yaml)
        print("#" * 25 + " AXOS REF LAG INTERFACE CFG " + "#" * 25)
        print(gen_lag_cfg)
        print("#" * 70)

    elif operation == '16':
        gen_mem_cfg = gen_tmpl_direct(lag_mem_cfg_jinja, lag_mem_cfg_yaml)
        print("#" * 25 + " AXOS REF INTERFACE LAG MEMEMBER CFG " + "#" * 25)
        print(gen_mem_cfg)
        print("#" * 70)

    elif operation == '17':
        gen_gos_cfg = gen_tmpl_direct(gos_cfg_jinja, gos_cfg_yaml )
        print("#" * 25 + " AXOS REF GRADE OF SERVICE CFG " + "#" * 25)
        print(gen_gos_cfg)
        print("#" * 70)

    elif operation == '18':
        gen_rg_cfg = gen_tmpl_direct(rg_mgmt_profile_cfg_jinja, rg_mgmt_profile_cfg_yaml )
        print("#" * 25 + " AXOS REF RG-MGMT-PROFILE CFG " + "#" * 25)
        print(gen_rg_cfg)
        print("#" * 70)

    elif operation == '19':
        gen_cm_cfg = gen_tmpl_direct(classmap_cfg_jinja, classmap_cfg_yaml )
        print("#" * 25 + " AXOS REF CLASS-MAP CFG " + "#" * 25)
        print(gen_cm_cfg)
        print("#" * 70)

    elif operation == '20':
        gen_pm_cfg = gen_tmpl_direct(policymap_cfg_jinja, policymap_cfg_yaml )
        print("#" * 25 + " AXOS REF POLICY-MAP CFG " + "#" * 25)
        print(gen_pm_cfg)
        print("#" * 70)

    elif operation == '21':
        gen_mb_cfg = gen_tmpl_direct(mb_dhcp_cfg_jinja, mb_dhcp_cfg_yaml )
        print("#" * 25 + " AXOS REF DHCP & MULTIBIND INT CFG " + "#" * 15)
        print(gen_mb_cfg)
        print("#" * 70)

    elif operation == '29':
        with open('/tmp/full_config.yaml', 'w') as f0:
           for item in list_of_yaml:
               f0.write("%s\n" % item)
           f0.close()
        with open('/tmp/full_config.j2', 'w') as f1:
           for item in list_of_jinja:
               f1.write("%s\n" % item)
           f1.close()
        full_jinja = '/tmp/full_config.j2'
        full_yaml = '/tmp/full_config.yaml'
        gen_full_cfg = gen_tmpl(full_jinja, full_yaml )
        with open("/tmp/full_ref_config.txt", "w") as f2:
            f2.write(gen_full_cfg )
            f2.close()
        print(gen_full_cfg)


    elif operation == '30':
        print(mylist)

    else:
        print(
            'Selection invalid; Please run again.'
        )

    again()


def again():
    list_again = input('''
Would you like to see the menu again? (Y/N)
''')
    if list_again.upper() == 'Y':
        list()
    elif list_again.upper() == 'N':
        print('OK. Ciao and Thanks!')
    else:
        again()



###############################################################################
# MAIN
###############################################################################
def main():
    """
    CALL ALL FUNCTIONS
    """
    msg0 = "Starting Calix push configuration program"
    print(msg0)
    start_logging = init_logger()
    if start_logging:
        logging.info("Script is starting")
    #cfg_list = gen_tmpl(J2_FILE, J2_YAML)
    #if cfg_list:
    #    logging.info("Jinja2 template has been rendered")
    #result = send_cfg_cmds(DEVICE_DICT, cfg_list)
    #pp(result)
    list()


###############################################################################
# CALL MAIN
###############################################################################
if __name__ == "__main__":
    main()
