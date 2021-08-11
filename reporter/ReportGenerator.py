import logging


class ReportGenerator:
    def __init__(
        self,
        telegram,
        pump_emoji="\U0001F7E2",  # 🟢
        dump_emoji="\U0001F534",  # 🔴
    ):
        self.telegram = telegram
        self.pump_emoji = pump_emoji
        self.dump_emoji = dump_emoji

        self.logger = logging.getLogger("report-generator")

    def send_pump_message(self, interval, symbol, change, price, is_alert_chat=False):
        self.telegram.send_message(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.pump_emoji, interval, symbol, change * 100, price
            ),
            is_alert_chat,
        )

    def send_dump_message(self, interval, symbol, change, price, is_alert_chat=False):
        self.telegram.send_message(
            "{0} *[{1} Interval] {2}* | Change: _{3:.3f}%_ | Price: _{4:.10f}_".format(
                self.dump_emoji, interval, symbol, change * 100, price
            ),
            is_alert_chat,
        )

    def send_new_listings(self, symbols_to_add):
        message = """*New Listings*
                     {0} new pairs found, adding to monitored list.

                     *Adding Pairs:*
                     """.format(
            len(symbols_to_add)
        )

        for symbol in symbols_to_add:
            message += "- _{0}_\n".format(symbol)

        self.telegram.send_news_message(message, is_alert_chat=True)

    def send_pump_dump_message(
        self,
        asset,
        chart_intervals,
        dump_enabled=True,
    ):
        change = 0
        tmpChange = 0
        tmpInterval = 0
        no_of_alerts = 0
        message = ""
        for interval in chart_intervals:

            change = asset[interval]["change_alert"]

            if change > 0:
                tmpChange = change
                tmpInterval = interval
                no_of_alerts += 1
                message += "{0} *[{1} Interval]* Change: _{2:.3f}%_ | Price: _{3:.10f}_\n".format(
                    self.pump_emoji,
                    interval,
                    change * 100,
                    asset["price"][-1],
                )

            if change < 0 and dump_enabled:
                tmpChange = change
                tmpInterval = interval
                no_of_alerts += 1
                message += "{0} *[{1} Interval]* Change: _{2:.3f}%_ | Price: _{3:.10f}_\n".format(
                    self.dump_emoji,
                    interval,
                    change * 100,
                    asset["price"][-1],
                )

        if no_of_alerts == 1:
            if change > 0:
                self.send_pump_message(
                    tmpInterval,
                    asset["symbol"],
                    tmpChange,
                    asset["price"][-1],
                )
            if change < 0 and dump_enabled:
                self.send_dump_message(
                    tmpInterval,
                    asset["symbol"],
                    tmpChange,
                    asset["price"][-1],
                )

        # Send summarized alert if multiple at the same extraction
        if no_of_alerts > 1:
            message = (
                "*{0}* | {1} Summarized Alerts\n\n".format(
                    asset["symbol"], no_of_alerts
                )
                + message
            )
            self.telegram.send_news_message(message)

    def send_top_pump_dump_statistics_report(
        self,
        assets,
        interval,
        top_pump_enabled=True,
        top_dump_enabled=True,
        additional_stats_enabled=True,
        no_of_reported_coins=5,
    ):
        message = "*[{0} Interval]*\n\n".format(interval)

        if top_pump_enabled:
            pump_sorted_list = sorted(
                assets,
                key=lambda item: item[interval]["change_top_report"],
                reverse=True,
            )[0:no_of_reported_coins]

            message += "{0} *Top {1} Pumps*\n".format(
                self.pump_emoji, no_of_reported_coins
            )

            for asset in pump_sorted_list:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval]["change_top_report"] * 100
                )
            message += "\n"

        if top_dump_enabled:
            dump_sorted_list = sorted(
                assets, key=lambda item: item[interval]["change_top_report"]
            )[0:no_of_reported_coins]

            message += "{0} *Top {1} Dumps*\n".format(
                self.dump_emoji, no_of_reported_coins
            )

            for asset in dump_sorted_list:
                message += "- {0}: _{1:.2f}_%\n".format(
                    asset["symbol"], asset[interval]["change_top_report"] * 100
                )

        if additional_stats_enabled:
            if top_pump_enabled or top_dump_enabled:
                message += "\n"
            message += self.generate_additional_statistics_report(assets, interval)

        self.telegram.send_report_message(message, is_alert_chat=True)

    def generate_additional_statistics_report(self, assets, interval):
        up = 0
        down = 0
        sum_change = 0

        for asset in assets:
            if asset[interval]["change_top_report"] > 0:
                up += 1
            elif asset[interval]["change_top_report"] < 0:
                down += 1

            sum_change += asset[interval]["change_top_report"]

        avg_change = sum_change / len(assets)

        return "*Average Change:* {0:.2f}%\n {1} {2} / {3} {4}".format(
            avg_change * 100,
            self.pump_emoji,
            up,
            self.dump_emoji,
            down,
        )
