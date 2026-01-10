class DatasetWithCWEs:
    def __init__(self, data):
        """
        Initialize the dataset with CVEs.

        :param data: List or dictionary containing CVE data.
        """
        self.data = data

    def filter_by_severity(self, severity):
        """
        Filter the dataset by severity level.

        :param severity: Severity level to filter by (e.g., 'low', 'medium', 'high', 'critical').
        :return: Filtered list of CVEs.
        """
        return [cve for cve in self.data if cve.get('severity') == severity]

    def get_cve_by_id(self, cve_id):
        """
        Retrieve a CVE by its ID.

        :param cve_id: The ID of the CVE to retrieve.
        :return: The CVE data or None if not found.
        """
        for cve in self.data:
            if cve.get('id') == cve_id:
                return cve
        return None

    def count_by_severity(self):
        """
        Count the number of CVEs by severity level.

        :return: Dictionary with severity levels as keys and counts as values.
        """
        severity_count = {}
        for cve in self.data:
            severity = cve.get('severity', 'unknown')
            severity_count[severity] = severity_count.get(severity, 0) + 1
        return severity_count