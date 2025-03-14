import os
from datetime import datetime

def generate_html_report(test_results):
    """Generate HTML reports for test results."""
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    # Calculate summary statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result["status"] == "Pass")
    failed_tests = total_tests - passed_tests

    # Generate summary report
    summary_html = f"""
    <html>
    <head>
        <title>Test Summary Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            a {{ text-decoration: none; color: inherit; }}
            .pass {{ color: green; }}
            .fail {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Test Summary Report</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d")}</p>
        <p>Total Tests: {total_tests}</p>
        <p>Passed Tests: {passed_tests}</p>
        <p>Failed Tests: {failed_tests}</p>
        <table>
            <tr>
                <th>Test Case ID</th>
                <th>Status</th>
                <th>Total Steps</th>
                <th>Passed Steps</th>
                <th>Failed Steps</th>
                <th>Elapsed Time (seconds)</th>
            </tr>
    """

    for result in test_results:
        status_class = "pass" if result["status"] == "Pass" else "fail"
        total_steps = len(result["steps"])
        passed_steps = sum(1 for step in result["steps"] if step["status"] == "Pass")
        failed_steps = total_steps - passed_steps
        elapsed_time = result["elapsed_time"]
        summary_html += f"""
            <tr>
                <td><a href="test_case_{result['test_case_id']}.html">{result['test_case_id']}</a></td>
                <td class="{status_class}">{result['status']}</td>
                <td>{total_steps}</td>
                <td>{passed_steps}</td>
                <td>{failed_steps}</td>
                <td>{elapsed_time}</td>
            </tr>
        """

    summary_html += """
        </table>
    </body>
    </html>
    """

    with open(os.path.join(report_dir, "summary_report.html"), "w") as f:
        f.write(summary_html)

    # Generate detailed reports for each test case
    for result in test_results:
        detailed_html = f"""
        <html>
        <head>
            <title>Test Case {result['test_case_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Test Case {result['test_case_id']}</h1>
            <p>Status: <span class="{'pass' if result['status'] == 'Pass' else 'fail'}">{result['status']}</span></p>
            <table>
                <tr>
                    <th>Step No</th>
                    <th>Step Description</th>
                    <th>Expected Result</th>
                    <th>Actual Result</th>
                    <th>Status</th>
                    <th>Screenshot</th>
                </tr>
        """

        for step in result["steps"]:
            status_class = "pass" if step["status"] == "Pass" else "fail"
            screenshot = f"<a target='_blank' href={step.get('screenshot_path', '')}><img style='height: 30px;width: 35px;' src='../assets/image_upload_icons.svg' alt='Screenshot'> </a>" if step.get("screenshot_path") else "No screenshot"
            detailed_html += f"""
                <tr>
                    <td>{step['step_no']}</td>
                    <td>{step['step_desc']}</td>
                    <td>{step['expected_result']}</td>
                    <td>{step['actual_result']}</td>
                    <td class="{status_class}">{step['status']}</td>
                    <td>{screenshot}</td>
                </tr>
            """

        detailed_html += """
            </table>
        </body>
        </html>
        """

        with open(os.path.join(report_dir, f"test_case_{result['test_case_id']}.html"), "w") as f:
            f.write(detailed_html)

    print(f"HTML reports generated in '{report_dir}' directory.")
