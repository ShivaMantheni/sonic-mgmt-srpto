"""
MAC ACL API Module
Author: Shiva
2026

This module provides API functions for MAC ACL operations specific to
show commands and verification that are not covered in the main acl.py module.
"""

from spytest import st
from utilities.common import filter_and_select
import utilities.utils as util_obj


def create_mac_acl_rule(dut, table_name, rule_seq, packet_action, src_mac="any",
                        dst_mac="any", cli_type="", **kwargs):
    """
    Wrapper function to create MAC ACL rule with correct command syntax for klish.

    This function constructs the proper command with "host" keyword for specific MAC addresses.

    :param dut: Device Under Test
    :param table_name: ACL table name
    :param rule_seq: Rule sequence number
    :param packet_action: Action (permit/deny)
    :param src_mac: Source MAC address (default: "any")
    :param dst_mac: Destination MAC address (default: "any")
    :param cli_type: CLI type
    :param kwargs: Additional parameters
    :return: True if successful, False otherwise

    Example:
        result = create_mac_acl_rule(dut, table_name="ACL_deny", rule_seq=10,
                                     packet_action="deny", src_mac="any",
                                     dst_mac="52:54:00:D3:79:35")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if cli_type == "klish":
        # Build command with proper syntax
        commands = []
        commands.append("mac access-list {}".format(table_name))

        # Construct the rule command
        cmd_parts = ["seq", str(rule_seq), packet_action]

        # Add source MAC with "host" keyword if not "any"
        if src_mac == "any":
            cmd_parts.append("any")
        else:
            cmd_parts.append("any")  # Source is "any" in our test cases

        # Add destination MAC with "host" keyword if not "any"
        if dst_mac == "any":
            cmd_parts.append("any")
        else:
            # Extract MAC address if it has mask notation
            if "/" in dst_mac:
                mac_addr = dst_mac.split("/")[0]
                cmd_parts.extend(["host", mac_addr])
            else:
                cmd_parts.extend(["host", dst_mac])

        # Add additional parameters if provided
        if kwargs.get("vlan_id"):
            cmd_parts.extend(["vlan", str(kwargs["vlan_id"])])

        commands.append(" ".join(cmd_parts))
        commands.append("exit")

        # Execute command
        skip_error_check = kwargs.get("skip_error_check", False)
        output = st.config(dut, commands, type=cli_type, skip_error_check=skip_error_check)

        # Check for errors if not skipping
        if not skip_error_check:
            if "Error" in output or "error" in output:
                st.log("Failed to create MAC ACL rule: {}".format(output))
                return False

        return True
    else:
        # For other CLI types, use the existing API
        from apis.qos.acl import create_acl_rule
        return create_acl_rule(dut, table_name=table_name, rule_name="RULE_{}".format(rule_seq),
                              rule_seq=rule_seq, packet_action=packet_action,
                              src_mac=src_mac, dst_mac=dst_mac, acl_type="L2",
                              cli_type=cli_type, **kwargs)


def show_mac_access_lists(dut, table_name=None, cli_type=""):
    """
    API to execute 'show mac access-lists' command

    :param dut: Device Under Test
    :param table_name: Optional - specific MAC ACL table name
    :param cli_type: CLI type (klish, click, rest)
    :return: Parsed output as list of dictionaries

    Example:
        output = show_mac_access_lists(dut, table_name="ACL_deny")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if cli_type == "klish":
        command = 'show mac access-lists'
        if table_name:
            command += ' {}'.format(table_name)

        output = st.show(dut, command, type=cli_type, skip_error_check=True)
        return output if output else []

    elif cli_type == "click":
        st.log("show mac access-lists not supported in click CLI, using acl.show_acl_table")
        from apis.qos.acl import show_acl_table
        return show_acl_table(dut, acl_table=table_name)

    else:
        st.log("Unsupported CLI type: {}".format(cli_type))
        return []


def show_mac_access_group(dut, interface=None, cli_type=""):
    """
    API to execute 'show mac access-group' command

    Note: The 'show mac access-group' command does NOT support interface filtering.
    It always shows all interfaces. The interface parameter is used for
    post-processing filtering only.

    :param dut: Device Under Test
    :param interface: Optional - filter results by interface name (post-processing)
    :param cli_type: CLI type (klish, click, rest)
    :return: Parsed output as list of dictionaries

    Example:
        output = show_mac_access_group(dut, interface="Ethernet16")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if cli_type == "klish":
        # Note: "show mac access-group" does NOT accept interface parameter
        # Always show all interfaces
        command = 'show mac access-group'

        output = st.show(dut, command, type=cli_type, skip_error_check=True)

        # If interface specified, filter results in Python
        if interface and output:
            filtered_output = []
            for entry in output:
                if entry.get('interface') == interface:
                    filtered_output.append(entry)
            return filtered_output

        return output if output else []

    elif cli_type == "click":
        st.log("show mac access-group not supported in click CLI")
        return []

    else:
        st.log("Unsupported CLI type: {}".format(cli_type))
        return []


def verify_mac_access_group(dut, interface=None, acl_name=None, direction=None, cli_type="", **kwargs):
    """
    API to verify MAC ACL binding to interface

    :param dut: Device Under Test
    :param interface: Interface name to verify
    :param acl_name: ACL name to verify
    :param direction: Direction (ingress/egress)
    :param cli_type: CLI type
    :param kwargs: Additional parameters
    :return: True if verification passes, False otherwise

    Example:
        result = verify_mac_access_group(dut, interface="Ethernet16",
                                         acl_name="ACL_deny", direction="ingress")
    """
    output = show_mac_access_group(dut, interface=interface, cli_type=cli_type)

    if not output:
        st.error("No MAC ACL bindings found")
        return False

    # Build match criteria
    match_dict = {}
    if interface:
        match_dict['interface'] = interface
    if acl_name:
        match_dict['acl_name'] = acl_name
    if direction:
        match_dict['direction'] = direction.capitalize()

    # Add any additional kwargs
    for key, value in kwargs.items():
        if key not in ['cli_type', 'return_output']:
            match_dict[key] = value

    if kwargs.get('return_output'):
        return output

    # Verify each criterion
    for key, expected_value in match_dict.items():
        entries = filter_and_select(output, None, {key: expected_value})
        if not entries:
            st.error("Match not found for {}: Expected - {}, Actual output - {}".format(
                key, expected_value, output))
            return False

    return True


def verify_mac_access_list(dut, table_name=None, rule_seq=None, action=None,
                           src_mac=None, dst_mac=None, cli_type="", **kwargs):
    """
    API to verify MAC ACL rule configuration

    :param dut: Device Under Test
    :param table_name: ACL table name
    :param rule_seq: Rule sequence number
    :param action: Action (permit/deny)
    :param src_mac: Source MAC address
    :param dst_mac: Destination MAC address
    :param cli_type: CLI type
    :param kwargs: Additional parameters
    :return: True if verification passes, False otherwise

    Example:
        result = verify_mac_access_list(dut, table_name="ACL_deny",
                                        rule_seq=10, action="deny",
                                        dst_mac="52:54:00:D3:79:35")
    """
    output = show_mac_access_lists(dut, table_name=table_name, cli_type=cli_type)

    if not output:
        st.error("No MAC ACL rules found")
        return False

    # Build match criteria
    match_dict = {}
    if table_name:
        match_dict['access_list_name'] = table_name
    if rule_seq is not None:
        match_dict['rule_no'] = str(rule_seq)
    if action:
        match_dict['action'] = action.lower()
    if src_mac:
        match_dict['src_mac_address'] = src_mac
    if dst_mac:
        match_dict['dst_mac_address'] = dst_mac

    # Add any additional kwargs
    for key, value in kwargs.items():
        if key not in ['cli_type', 'return_output']:
            match_dict[key] = value

    if kwargs.get('return_output'):
        return output

    # Verify each criterion
    for key, expected_value in match_dict.items():
        entries = filter_and_select(output, None, {key: expected_value})
        if not entries:
            st.error("Match not found for {}: Expected - {}, Actual output - {}".format(
                key, expected_value, output))
            return False

    return True


def delete_mac_acl_rule(dut, table_name, rule_seq, cli_type=""):
    """
    API to delete a specific MAC ACL rule

    :param dut: Device Under Test
    :param table_name: ACL table name
    :param rule_seq: Rule sequence number to delete
    :param cli_type: CLI type
    :return: True if successful, False otherwise

    Example:
        result = delete_mac_acl_rule(dut, table_name="ACL_deny", rule_seq=10)
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if cli_type == "klish":
        commands = [
            "mac access-list {}".format(table_name),
            "no seq {}".format(rule_seq),
            "exit"
        ]
        output = st.config(dut, commands, type=cli_type, skip_error_check=True)
        if "Error" in output or "error" in output:
            st.log("Failed to delete MAC ACL rule: {}".format(output))
            return False
        return True

    else:
        st.log("Unsupported CLI type for delete_mac_acl_rule: {}".format(cli_type))
        return False


def delete_mac_acl_table(dut, table_name, cli_type=""):
    """
    API to delete MAC ACL table

    :param dut: Device Under Test
    :param table_name: ACL table name to delete
    :param cli_type: CLI type
    :return: True if successful, False otherwise

    Example:
        result = delete_mac_acl_table(dut, table_name="ACL_deny")
    """
    cli_type = st.get_ui_type(dut, cli_type=cli_type)

    if cli_type == "klish":
        commands = [
            "no mac access-list {}".format(table_name)
        ]
        output = st.config(dut, commands, type=cli_type, skip_error_check=True)
        if "Error" in output or "error" in output:
            st.log("Failed to delete MAC ACL table: {}".format(output))
            return False
        return True

    else:
        st.log("Unsupported CLI type for delete_mac_acl_table: {}".format(cli_type))
        return False


def unbind_mac_access_group(dut, interface, acl_name, direction="in", cli_type=""):
    """
    API to unbind MAC ACL from interface

    :param dut: Device Under Test
    :param interface: Interface name
    :param acl_name: ACL name to unbind
    :param direction: Direction (in/out)
    :param cli_type: CLI type
    :return: True if successful, False otherwise

    Example:
        result = unbind_mac_access_group(dut, interface="Ethernet16",
                                         acl_name="ACL_deny", direction="in")
    """
    from apis.qos.acl import config_access_group

    result = config_access_group(dut,
                                  acl_type="mac",
                                  table_name=acl_name,
                                  port=interface,
                                  access_group_action=direction,
                                  config="no",
                                  cli_type=cli_type,
                                  skip_error_check=True)
    return result
