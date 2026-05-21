# Phase 0d Operational Decisions

> Danh sach quyet dinh ngan de user xac nhan truoc khi dong Phase 0d va mo Phase 1.

## Confirmation status

- 2026-05-21: user da xac nhan maintenance model `Preventive Maintenance` / `Corrective Maintenance`
- 2026-05-21: user da xac nhan `Preventive Maintenance window = 18:00-23:30 ICT, thu Hai-Chu nhat`
- 2026-05-21: user da xac nhan item 1-10 ben duoi

## Confirm items

Ban de xuat duoi day duoc dien san theo boi canh hien tai (solo dev, local timezone `Asia/Bangkok`).
Neu dong y, giu nguyen. Neu khong, sua truc tiep tung dong.

```text
1. Single deployer cho cua so Phase 1:
   YES / Phong Bao

2. Stop-the-line authority khi gate Phase 1 fail:
   YES / Phong Bao

3. Reviewer P0 cho PR `[move]` dau tien:
   YES / Phong Bao (self-review voi checklist bat buoc)

4. Coordination channel su dung khi deploy / revert:
   YES / thread nay + git commit history + docs/refactor/incidents/

5. Railway production workspace log retention da verify:
   YES / Hobby / 7-Day Log History

6. Maintenance model cho Phase 1 deploy:
   YES / Preventive Maintenance cho `[move]` va runtime `[fix]`
   YES / Corrective Maintenance chi dung cho hotfix production ngoai ke hoach

7. Preventive Maintenance window cho PR `[move]` P0 admin:
   YES / 18:00-23:30 ICT (Asia/Bangkok), thu Hai-Chu nhat; uu tien P0 runtime change trong 20:00-23:00 neu can monitoring lien mach

8. Corrective Maintenance rule:
   YES / cho phep deploy ngoai khung gio neu la hotfix production, nhung van phai giu single-deployer + stop-the-line + incident log + post-deploy smoke

9. Co chap nhan known deviation hien tai:
   `/api/admin/users` khong emit `CREATE_USER` audit,
   local baseline dung `/admin/api/users`
   YES / tam chap nhan cho den truoc khi cham domain `admin_users`; KHONG cho phep PR Phase 1.x nao dong vao `admin_users` neu deviation chua duoc fix

10. First `[move]` PR target sau khi dong 0d:
   YES / `admin_login_logout`
```

## Closure rule

Item 1-10 da duoc user xac nhan.
Phase 0d operational sign-off da du dieu kien de mo Phase 1.
