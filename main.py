async def _run_cycle(self):
    """Run one analysis cycle"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Cycle #{self.cycle_count + 1}")
    
    # Fetch data
    data = await self.fetcher.fetch_multiple_timeframes()
    
    # Tampilkan info data source
    source_info = self.fetcher.get_data_source_info()
    if source_info:
        print(f"📊 Data sources: {source_info}")
    
    if not data or all(df is None for df in data.values()):
        print("⚠️ Tidak ada data, skip cycle ini")
        return
    
    # Analyze data
    analysis_results = {}
    for timeframe, df in data.items():
        if df is not None:
            analysis_results[timeframe] = self.analyzer.analyze(df)
    
    # Generate signals
    signals = self.generator.generate_signals(analysis_results)
    
    # Process signals
    if signals:
        print(f"✅ {len(signals)} sinyal ditemukan")
        for signal in signals:
            await self._process_signal(signal)
    else:
        print("ℹ️ Tidak ada sinyal valid")
