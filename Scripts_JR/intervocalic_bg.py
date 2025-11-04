# Pattern I need to find intervocalic -b- and -g- (also Cross-boundary intervocalic context)

'''
Pattern 1: Word-internal intervocalic b/g
Example: "abito" -> finds 'b' between 'a' and 'i'
r'[aeiouàèéìòù][bg][aeiouàèéìòù]'
'''

'''
Pattern 2: Cross-boundary intervocalic b/g
vowel + space(s) + [b or g] + vowel (across word boundary)
r'[aeiouàèéìòù]\s+[bg][aeiouàèéìòù]
'''

