# Copyright (c) 2010 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


import itertools


class TemplateWriter(object):
  '''Abstract base class for writing policy templates in various formats.
  The methods of this class will be called by PolicyTemplateGenerator.
  '''

  def __init__(self, platforms, config, messages):
    '''Initializes a TemplateWriter object.

    Args:
      platforms: List of platforms for which this writer can write policies.
      config: A dictionary of information required to generate the template.
        It contains some key-value pairs, including the following examples:
          'build': 'chrome' or 'chromium'
          'branding': 'Google Chrome' or 'Chromium'
          'mac_bundle_id': The Mac bundle id of Chrome. (Only set when building
            for Mac.)
      messages: List of all the message strings from the grd file. Most of them
        are also present in the policy data structures that are passed to
        methods. That is the preferred way of accessing them, this should only
        be used in exceptional cases. An example for its use is the
        IDS_POLICY_WIN_SUPPORTED_WINXPSP2 message in ADM files, because that
        cannot be associated with any policy or group.
    '''
    self.platforms = platforms
    self.config = config
    self.messages = messages

  def IsPolicySupported(self, policy):
    '''Checks if the given policy is supported by the writer.
    In other words, the set of platforms supported by the writer
    has a common subset with the set of platforms that support
    the policy.

    Args:
      policy: The dictionary of the policy.

    Returns:
      True if the writer chooses to include 'policy' in its output.
    '''
    if '*' in self.platforms:
      # Currently chrome_os is only catched here.
      return True
    for supported_on in policy['supported_on']:
      for supported_on_platform in supported_on['platforms']:
        if supported_on_platform in self.platforms:
          return True
    return False

  def _GetPoliciesForWriter(self, group):
    '''Filters the list of policies in the passed group that are supported by
    the writer.

    Args:
      group: The dictionary of the policy group.

    Returns: The list of policies of the policy group that are compatible
      with the writer.
    '''
    if not 'policies' in group:
      return []
    result = []
    for policy in group['policies']:
      if self.IsPolicySupported(policy):
        result.append(policy)
    return result

  def Init(self):
    '''Initializes the writer. If the WriteTemplate method is overridden, then
    this method must be called as first step of each template generation
    process.
    '''
    pass

  def WriteTemplate(self, template):
    '''Writes the given template definition.

    Args:
      template: Template definition to write.

    Returns:
      Generated output for the passed template definition.
    '''
    self.Init()
    self.BeginTemplate()
    for policy in template:
      if policy['type'] == 'group':
        child_policies = self._GetPoliciesForWriter(policy)
        if child_policies:
          # Only write nonempty groups.
          self.BeginPolicyGroup(policy)
          for child_policy in child_policies:
            # Nesting of groups is currently not supported.
            self.WritePolicy(child_policy)
          self.EndPolicyGroup()
      elif self.IsPolicySupported(policy):
        self.WritePolicy(policy)
    self.EndTemplate()
    return self.GetTemplateText()

  def WritePolicy(self, policy):
    '''Appends the template text corresponding to a policy into the
    internal buffer.

    Args:
      policy: The policy as it is found in the JSON file.
    '''
    raise NotImplementedError()

  def BeginPolicyGroup(self, group):
    '''Appends the template text corresponding to the beginning of a
    policy group into the internal buffer.

    Args:
      group: The policy group as it is found in the JSON file.
    '''
    pass

  def EndPolicyGroup(self):
    '''Appends the template text corresponding to the end of a
    policy group into the internal buffer.
    '''
    pass

  def BeginTemplate(self):
    '''Appends the text corresponding to the beginning of the whole
    template into the internal buffer.
    '''
    raise NotImplementedError()

  def EndTemplate(self):
    '''Appends the text corresponding to the end of the whole
    template into the internal buffer.
    '''
    pass

  def GetTemplateText(self):
    '''Gets the content of the internal template buffer.

    Returns:
      The generated template from the the internal buffer as a string.
    '''
    raise NotImplementedError()
