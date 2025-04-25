# インストールとセットアップ

## 前提条件：

Docker および Docker Compose がインストールされていることを前提としています。
以下は、WSL2でのローカルデプロイを想定した手順です。

- Ubuntu 22.04
- Docker 24.0以上
- Docker Compose 2.20以上
- WSL2（Windows Subsystem for Linux 2）
- メモリ: 8GB以上推奨
- ストレージ: 1GB以上の空き容量


## 手順：

1. リポジトリをクローン
   ```sh
   git clone https://github.com/Project-LINKS-mlitoss/gtfs-analysis-tool.git

   cd gtfs-analysis-tool
   ```
2. 環境変数の設定
   `.env.sample` を `.env` にコピーし、適宜編集してください。
   ```sh
   cp .env.sample .env
   ```
      `.env` には以下の変数を設定できます（値は環境に応じて適宜変更してください）。
   ```
   SECRET_KEY=your-secret-key-here
   DJANGO_DEBUG=1
   DB_USER=postgres
   DB_PASSWORD=postgres
   GEOSERVER_USER=admin
   GEOSERVER_PASSWORD=geoserver
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@localhost
   DJANGO_SUPERUSER_PASSWORD=admin1112
   ```

   `SECRET_KEY` は必ず独自の値に変更してください。

3. Dockerイメージをビルドし、コンテナを起動
   ```sh
   docker compose -f compose-dev.yml up --build
   ```
   - 初回の起動には時間がかかります。
   - PostgreSQL → Django → Node.js & Nginx の順で起動します。
   - OpenTripPlanner、GeoServer は非同期で起動します。
   - `nginx` の起動ログに `Configuration complete; ready for start up` が表示されれば成功です。

4. データベースのインポート
   ```sh
   docker compose -f compose-dev.yml cp ./traffic_info.dmp db:/tmp/traffic_info.dmp
   docker compose -f compose-dev.yml exec -it db pg_restore -U postgres -d traffic_info /tmp/traffic_info.dmp
   ```

5. データ準備
- `.dmp` ファイルを `data/` ディレクトリに配置する
  ```sh
  docker compose -f compose-dev.yml exec -it web python manage.py convert_current_gtfs
  docker compose -f compose-dev.yml exec -it web python manage.py download_nodata
  ```

6. リソースの再読み込みを行う。
   ```sh
   docker compose -f ./compose-dev.yml restart geoserver
   docker compose -f ./compose-dev.yml restart otp
   docker compose -f ./compose-dev.yml restart db
   docker compose -f ./compose-dev.yml restart web
   ```

7. 動作確認
`http://localhost/` にアクセスし、ログイン画面が表示されることを確認。


### クリーンアップ手順
コンテナとデータを完全に削除する
```sh
# コンテナの停止と削除
docker compose -f compose-dev.yml down

# ボリュームの削除（データベースのデータも削除されます）
docker compose -f compose-dev.yml down -v

# イメージの削除
docker compose -f compose-dev.yml down --rmi all
```