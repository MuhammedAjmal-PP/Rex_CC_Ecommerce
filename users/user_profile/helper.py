
PINCODE_STATE_MAP = {
    (11, 11): ["Delhi", "New Delhi"],
    (12, 13): ["Haryana"],
    (14, 16): ["Punjab", "Chandigarh"],
    (17, 17): ["Himachal Pradesh"],
    (18, 19): ["Jammu and Kashmir", "Jammu & Kashmir", "Ladakh"],
    (20, 28): ["Uttar Pradesh", "Uttarakhand"],
    (30, 34): ["Rajasthan"],
    (36, 39): ["Gujarat", "Daman and Diu", "Dadra and Nagar Haveli"],
    (40, 44): ["Maharashtra", "Goa"],
    (45, 48): ["Madhya Pradesh"],
    (49, 49): ["Chhattisgarh"],
    (50, 50): ["Telangana"],
    (51, 53): ["Andhra Pradesh", "Telangana"],
    (56, 59): ["Karnataka"],
    (60, 64): ["Tamil Nadu", "Puducherry"],
    (67, 69): ["Kerala", "Lakshadweep"],
    (70, 74): ["West Bengal", "Andaman and Nicobar Islands"],
    (75, 77): ["Odisha"],
    (78, 78): ["Assam"],
    (79, 79): [
        "Arunachal Pradesh",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Tripura",
    ],
    (80, 85): ["Bihar", "Jharkhand"],
}


def get_expected_states(prefix: int) -> list[str]:
    for (start, end), states in PINCODE_STATE_MAP.items():
        if start <= prefix <= end:
            return states
    return []
