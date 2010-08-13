# Copyright (c) 2010 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


from template_writer import TemplateWriter


class MockWriter(TemplateWriter):
  '''Helper class for unit tests in policy_template_generator_unittest.py
  '''

  def __init__(self):
    pass

  def WritePolicy(self, policy_name, policy):
    pass

  def BeginPolicyGroup(self, group_name, group):
    pass

  def EndPolicyGroup(self):
    pass

  def BeginTemplate(self):
    pass

  def EndTemplate(self):
    pass

  def Prepare(self):
    pass

  def GetTemplateText(self):
    pass

  def Test(self):
    pass
