import unittest
from server_utils import remove_lonely_dash

class TestProcessNestedDict(unittest.TestCase):

    def test_process_nested_dict(self):
        # Test case 1: Nested dictionary with 'means' and '-'
        input_data = {
            'A2': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]],
                    '-': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        expected_output = {
            'A2': {
                'means': [[4, 5, 6]]
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test_empty_dict(self):
        # Test case 2: Empty dictionary
        input_data = {}
        expected_output = {}
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test1(self):
        # Test case 1: Nested dictionary with 'means' and '-'
        input_data = {
            'A': {
                'means': [[4, 5, 6]]
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]]
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test2(self):
        # Test case 1: Nested dictionary with 'means' and '-'
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test3(self):

        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]]
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test4(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A2': {
                    'means': [[7, 8, 9]]
                },
                'A3': {
                    'means': [[10, 11, 12]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A2': {
                    'means': [[7, 8, 9]]
                },
                'A3': {
                    'means': [[10, 11, 12]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test5(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]]
                },
                'A2': {
                    'means': [[10, 11, 12]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A2': {
                    'means': [[10, 11, 12]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test6(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]]
                },
                'A2': {
                    'means': [[10, 11, 12]]
                },
                'A3': {
                    'means': [[13, 14, 15]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A2': {
                    'means': [[10, 11, 12]]
                },
                'A3': {
                    'means': [[13, 14, 15]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test7(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]],
                    'A2': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]],
                    'A2': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test8(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]],
                    '-': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)
    
    def test9(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]],
                    'A2': {
                        'means': [[10, 11, 12]]
                    }
                },
                '-': {
                    'means': [[71, 81, 91]]
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[7, 8, 9]],
                    'A2': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test10(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]],
                    'A2': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A2': {
                    'means': [[10, 11, 12]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output)

    def test11(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[7, 8, 9]],
                    '-': {
                        'means': [[10, 11, 12]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]]
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 

    def test12(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]]
                    }
                },
                'A2': {
                    'means': [[27, 28, 29]],
                    'A4': {
                        'means': [[180, 181, 812]]
                    }
                },
                'A3': {
                    'means': [[677, 768, 769]],
                    '-': {
                        'means': [[1110, 111, 112]]
                    }
                },
                '-': {
                    'means': [[710, 801, 901]],
                    'A5': {
                        'means': [[100, 110, 102]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                },
                'A2': {
                    'means': [[27, 28, 29]],
                    'A4': {
                        'means': [[180, 181, 812]]
                    }
                },
                'A3': {
                    'means': [[677, 768, 769]],
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test13(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]]
                    },
                    'A1': {
                        'means': [[10, 110, 12]]
                    },
                    'A2': {
                        'means': [[100, 11, 102]]
                    },
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[10, 110, 12]]
                },
                'A2': {
                    'means': [[100, 11, 102]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test14(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A5': {
                            'means': [[10, 110, 12]]
                        },
                        '-': {
                            'means': [[130, 311, 312]]
                        }
                    },
                    'A2': {
                        'means': [[10, 110, 12]],
                        'A4': {
                            'means': [[10, 110, 12]]
                        },
                        '-': {
                            'means': [[130, 311, 312]]
                        }
                    }
                },
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A7': {
                            'means': [[10, 110, 12]]
                        },
                        '-': {
                            'means': [[130, 311, 312]]
                        }
                    },
                    'A3': {
                        'means': [[10, 110, 12]],
                        'A6': {
                            'means': [[10, 110, 12]]
                        },
                        '-': {
                            'means': [[130, 311, 312]]
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    'A2': {
                        'means': [[10, 110, 12]],
                        'A4': {
                            'means': [[10, 110, 12]]
                        }
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 

    def test15(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        '-': {
                            'means': [[130, 311, 312]]
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test16(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        '-': {
                            'means': [[130, 11, 312]]
                        },
                        'A2': {
                            'means': [[5, 85, 95]]
                        },
                        'A3': {
                            'means': [[75, 5, 5]]
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    'A2': {
                        'means': [[5, 85, 95]]
                    },
                    'A3': {
                        'means': [[75, 5, 5]]
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 

    def test17(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A3': {
                            'means': [[5, 851, 95]]
                        },
                        'A4': {
                            'means': [[75, 55, 5]]
                        }
                    },
                    'A1': {
                        'means': [[130, 3911, 3012]]
                    },
                    'A2': {
                        'means': [[130, 34411, 312]]
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[130, 3911, 3012]]
                },
                'A2': {
                    'means': [[130, 34411, 312]]
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test18(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A1': {
                            'means': [[5, 851, 95]],
                            '-': {
                                'means': [[5, 851, 95]],
                                'A2': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[5, 851, 95]],
                    'A2': {
                        'means': [[5, 851, 95]]
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test19(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A2': {
                            'means': [[5, 851, 95]],
                            '-': {
                                'means': [[5, 851, 95]],
                                'A3': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    'A2': {
                        'means': [[5, 851, 95]],
                        'A3': {
                            'means': [[5, 851, 95]]
                        }
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 

    def test20(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    'A1': {
                        'means': [[130, 311, 312]],
                        'A2': {
                            'means': [[5, 851, 95]],
                            '-': {
                                'means': [[5, 851, 95]],
                                'A3': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[130, 311, 312]],
                    'A2': {
                        'means': [[5, 851, 95]],
                        'A3': {
                            'means': [[5, 851, 95]]
                        }
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test21(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A1': {
                            'means': [[5, 851, 95]],
                            'A2': {
                                'means': [[5, 851, 95]],
                                'A3': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[5, 851, 95]],
                    'A2': {
                        'means': [[5, 851, 95]],
                        'A3': {
                            'means': [[5, 851, 95]]
                        }
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test22(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        '-': {
                            'means': [[5, 851, 95]],
                            '-': {
                                'means': [[5, 851, 95]],
                                'A1': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[5, 851, 95]]
                }
                }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test23(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                '-': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        'A1': {
                            'means': [[5, 851, 95]],
                            '-': {
                                'means': [[5, 851, 95]],
                                'A2': {
                                    'means': [[5, 81, 5]]
                                },
                                'A3': {
                                    'means': [[5, 851, 95]]
                                }
                            }
                        }
                    },
                    'A4': {
                        'means': [[130, 311, 312]],
                        'A5': {
                            'means': [[5, 85231, 95]],
                        },
                        'A6': {
                            'means': [[5, 851, 95]],
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A4': {
                    'means': [[130, 311, 312]],
                    'A5': {
                        'means': [[5, 85231, 95]],
                    },
                    'A6': {
                        'means': [[5, 851, 95]],
                    }
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 

    def test24(self):
        input_data = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        '-': {
                            'means': [[5, 851, 95]],
                        }
                    }
                }
            }
        }
        expected_output = {
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test25(self):
        input_data = {
            'DAMAC HILLS (2) - AMARGO ': {
                'Residential': {
                    '-': {
                        '-': {
                            'means': [
                                {
                                    'avgCapitalAppreciation2013': None,
                                    'avgCapitalAppreciation2029': 0.42701833505185927,
                                    'avg_meter_price_2013_2023': [
                                        None,
                                        None,
                                        None,
                                        None
                                    ],
                                    'avg_roi': None
                                }
                            ]
                        },
                        'means': [
                            {
                                'avgCapitalAppreciation2013': None,
                                'avgCapitalAppreciation2029': 0.42701833505185927,
                                'avg_meter_price_2013_2023': [
                                    None,
                                    None,
                                    None,
                                    None
                                ],
                                'avg_roi': None
                            }
                        ]
                    },
                    'means': [
                        {
                            'avgCapitalAppreciation2013': None,
                            'avgCapitalAppreciation2029': 0.42701833505185927,
                            'avg_meter_price_2013_2023': [
                                None,
                                None,
                                None
                            ],
                            'avg_roi': None
                        }
                    ]
                },
                'means': [
                    {
                        'avgCapitalAppreciation2013': None,
                        'avgCapitalAppreciation2029': 0.42701833505185927,
                        'avg_meter_price_2013_2023': [
                            None,
                            None,
                            None
                        ],
                        'avg_roi': None
                    }
                ]
            }
        }
        expected_output = {
            'DAMAC HILLS (2) - AMARGO ': {
                'Residential': {
                    'means': [
                        {
                            'avgCapitalAppreciation2013': None,
                            'avgCapitalAppreciation2029': 0.42701833505185927,
                            'avg_meter_price_2013_2023': [
                                None,
                                None,
                                None
                            ],
                            'avg_roi': None
                        }
                    ]
                },
                'means': [
                    {
                        'avgCapitalAppreciation2013': None,
                        'avgCapitalAppreciation2029': 0.42701833505185927,
                        'avg_meter_price_2013_2023': [
                            None,
                            None,
                            None
                        ],
                        'avg_roi': None
                    }
                ]
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
    
    def test26(self):
        input_data = {
            'B': {
                'means': [[34, 15, 46]],
                'B1': {
                    'means': [[3375, 835, 9533]],
                    '-': {
                        'means': [[1390, 3191, 3192]],
                        '-': {
                            'means': [[85, 851, 95]],
                        }
                    }
                }
            },
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                    '-': {
                        'means': [[130, 311, 312]],
                        '-': {
                            'means': [[5, 851, 95]],
                        }
                    }
                }
            }
        }
        expected_output = {
            'B': {
                'means': [[34, 15, 46]],
                'B1': {
                    'means': [[3375, 835, 9533]],
                }
            },
            'A': {
                'means': [[4, 5, 6]],
                'A1': {
                    'means': [[75, 85, 95]],
                }
            }
        }
        self.assertEqual(remove_lonely_dash(input_data), expected_output) 
if __name__ == '__main__':
    unittest.main()
