def claim_next_job(db, worker_id: str, lease_seconds: int = 300):
    # SQL conceptual: una fila, candado pesimista, sin doble ejecución
    return db.fetch_one("""
        update jobs
           set status='leased', worker_id=:worker_id,
               lease_until=now() + (:lease_seconds || ' seconds')::interval
         where id = (
             select id from jobs
              where status in ('pending','retry_scheduled')
                and run_after <= now()
              order by priority desc, created_at asc
              for update skip locked
              limit 1
         )
     returning *
    """, {"worker_id": worker_id, "lease_seconds": lease_seconds})
