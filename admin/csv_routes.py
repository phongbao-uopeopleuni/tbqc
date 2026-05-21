import csv
import pathlib
from flask import request, jsonify
from auth import permission_required

# Repo root — tính từ admin/ lên một cấp để định vị CSV files tại root
_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


def _get_csv_filename(sheet_name):
    mapping = {
        'sheet1': 'Data_TBQC_Sheet1.csv',
        'sheet2': 'Data_TBQC_Sheet2.csv',
        'sheet3': 'Data_TBQC_Sheet3.csv',
    }
    return mapping.get(sheet_name)


def _read_csv_file(sheet_name):
    """Đọc dữ liệu từ file CSV"""
    filename = _get_csv_filename(sheet_name)
    if not filename:
        return None, 'Sheet không hợp lệ'

    filepath = _BASE_DIR / filename
    if not filepath.exists():
        return None, f'File {filename} không tồn tại'

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return data, None
    except Exception as e:
        return None, f'Lỗi đọc file: {str(e)}'


def _write_csv_file(sheet_name, data):
    """Ghi dữ liệu vào file CSV"""
    filename = _get_csv_filename(sheet_name)
    if not filename:
        return 'Sheet không hợp lệ'

    filepath = _BASE_DIR / filename

    if not data:
        return 'Dữ liệu rỗng'

    try:
        headers = list(data[0].keys())
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        return None
    except Exception as e:
        return f'Lỗi ghi file: {str(e)}'


def register_admin_csv_routes(app):

    @app.route('/admin/api/csv-data/<sheet_name>', methods=['GET'])
    @permission_required('canViewDashboard')
    def get_csv_data(sheet_name):
        """API: Lấy dữ liệu từ CSV"""
        data, error = _read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})
        return jsonify({'success': True, 'data': data})

    @app.route('/admin/api/csv-data/<sheet_name>', methods=['POST'])
    @permission_required('canViewDashboard')
    def add_csv_row(sheet_name):
        """API: Thêm dòng mới vào CSV"""
        data, error = _read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})

        new_row = request.json

        # Tự động tăng STT/ID nếu chưa có
        if sheet_name in ['sheet1', 'sheet2']:
            if not new_row.get('STT') or new_row.get('STT') == '':
                max_stt = 0
                for row in data:
                    try:
                        stt_val = int(str(row.get('STT', 0) or 0))
                        if stt_val > max_stt:
                            max_stt = stt_val
                    except Exception:
                        pass
                new_row['STT'] = str(max_stt + 1)
        elif sheet_name == 'sheet3':
            if not new_row.get('ID') or new_row.get('ID') == '':
                max_id = 0
                for row in data:
                    try:
                        id_val = int(str(row.get('ID', 0) or 0))
                        if id_val > max_id:
                            max_id = id_val
                    except Exception:
                        pass
                new_row['ID'] = str(max_id + 1)

        # Đảm bảo có đủ các cột
        headers = list(data[0].keys()) if data else []
        for header in headers:
            if header not in new_row:
                new_row[header] = ''

        data.append(new_row)

        error = _write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})

        return jsonify({'success': True, 'message': 'Đã thêm dòng mới thành công'})

    @app.route('/admin/api/csv-data/<sheet_name>/<int:row_index>', methods=['PUT'])
    @permission_required('canViewDashboard')
    def update_csv_row(sheet_name, row_index):
        """API: Cập nhật dòng trong CSV"""
        data, error = _read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})

        if row_index < 0 or row_index >= len(data):
            return jsonify({'success': False, 'error': 'Chỉ số dòng không hợp lệ'})

        updated_row = request.json
        headers = list(data[0].keys())
        new_row = {header: updated_row.get(header, '') for header in headers}
        data[row_index] = new_row

        error = _write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})

        return jsonify({'success': True, 'message': 'Đã cập nhật thành công'})

    @app.route('/admin/api/csv-data/<sheet_name>/<int:row_index>', methods=['DELETE'])
    @permission_required('canViewDashboard')
    def delete_csv_row(sheet_name, row_index):
        """API: Xóa dòng trong CSV"""
        data, error = _read_csv_file(sheet_name)
        if error:
            return jsonify({'success': False, 'error': error})

        if row_index < 0 or row_index >= len(data):
            return jsonify({'success': False, 'error': 'Chỉ số dòng không hợp lệ'})

        data.pop(row_index)

        error = _write_csv_file(sheet_name, data)
        if error:
            return jsonify({'success': False, 'error': error})

        return jsonify({'success': True, 'message': 'Đã xóa thành công'})
